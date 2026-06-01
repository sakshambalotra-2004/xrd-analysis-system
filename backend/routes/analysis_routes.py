"""
routes/analysis_routes.py
==========================
Analysis Routes — REST endpoints that trigger and retrieve XRD analysis.

Endpoints
---------
POST /api/analysis/{file_id}
    Run the full 10-stage analysis pipeline for an uploaded file.

GET /api/analysis/{file_id}
    Retrieve stored analysis results for a file_id.

GET /api/analysis/{file_id}/peaks
    Return the detected peaks table as JSON.

GET /api/analysis/compounds
    List all standard compounds in the database.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel

from config import settings
from services.csv_reader import CSVReadError, CSVReader
from services.noise_filter import NoiseFilter
from services.peak_detector import PeakDetector
from services.peak_matcher import PeakMatcher
from services.crystal_analyzer import CrystalAnalyzer
from services.graph_generator import GraphGenerator
from services.report_generator import ReportGenerator
from utils.file_handler import FileHandler

logger = logging.getLogger(__name__)
router = APIRouter()

# Service singletons
csv_reader = CSVReader()
noise_filter = NoiseFilter()
peak_detector = PeakDetector()
peak_matcher = PeakMatcher()
crystal_analyzer = CrystalAnalyzer()
graph_generator = GraphGenerator()
report_generator = ReportGenerator()
file_handler = FileHandler()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class PeakRow(BaseModel):
    two_theta: float
    intensity: float
    fwhm_deg: float
    prominence: float


class MatchedPeakRow(BaseModel):
    two_theta_exp: float
    two_theta_std: float
    delta_two_theta: float
    d_spacing: float
    intensity_std: float
    h: int
    k: int
    l: int


class AnalysisResponse(BaseModel):
    file_id: str
    status: str
    compound_name: str
    formula: str
    crystal_system: str
    space_group: str
    confidence_score: float
    crystallite_size_nm: float
    mean_peak_shift_deg: float
    strain_indicator: str
    detected_phases: list[str]
    peaks: list[PeakRow]
    matched_peaks: list[MatchedPeakRow]
    graph_experimental: str
    graph_standard: str
    graph_overlay: str
    report_pdf: str


# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

def _run_pipeline(file_id: str, file_path: str) -> AnalysisResponse:
    """Execute the full 10-stage XRD analysis pipeline."""
    logger.info("Starting analysis pipeline for file_id=%s", file_id)

    # Stage 1 — CSV Reader
    df = csv_reader.load(file_path)

    # Stage 2 — Noise Filter
    df_smooth = noise_filter.filter(df)

    # Stage 3 — Peak Detector
    peaks_df = peak_detector.detect(df_smooth)

    # Stage 4 & 5 — Peak Matching + Similarity Scoring
    candidates = peak_matcher.match(peaks_df)
    best_match = candidates[0] if candidates else None

    # Stage 6–9 — Crystal Analysis
    analysis = crystal_analyzer.analyze(peaks_df, best_match, all_matches=candidates)

    # Stage 8 — Graph Visualisation
    graph_paths = graph_generator.generate_all(df_smooth, peaks_df, best_match, file_id)

    # Stage 10 — Report Generation
    pdf_path = report_generator.generate(file_id, analysis, peaks_df, graph_paths, best_match)

    # Persist results
    file_handler.save_analysis_result(file_id, analysis, pdf_path)
    # Persist peaks
    file_handler.save_peaks(file_id, [
        {
            "two_theta": round(float(r["two_theta"]), 4),
            "intensity": round(float(r["intensity"]), 2),
            "fwhm_deg": round(float(r["fwhm_deg"]), 4),
            "prominence": round(float(r["prominence"]), 2),
        }
        for _, r in peaks_df.iterrows()
    ])

    peaks_out = [
        PeakRow(
            two_theta=round(float(r["two_theta"]), 4),
            intensity=round(float(r["intensity"]), 2),
            fwhm_deg=round(float(r["fwhm_deg"]), 4),
            prominence=round(float(r["prominence"]), 2),
        )
        for _, r in peaks_df.iterrows()
    ]

    matched_peaks_out: list[MatchedPeakRow] = []
    if best_match:
        matched_peaks_out = [
            MatchedPeakRow(
                two_theta_exp=round(mp.two_theta_exp, 4),
                two_theta_std=round(mp.two_theta_std, 4),
                delta_two_theta=round(mp.delta_two_theta, 4),
                d_spacing=round(mp.d_spacing, 4),
                intensity_std=round(mp.intensity_std, 2),
                h=mp.h, k=mp.k, l=mp.l,
            )
            for mp in best_match.matched_peaks
        ]

    return AnalysisResponse(
        file_id=file_id,
        status="done",
        compound_name=analysis.primary_compound,
        formula=analysis.formula,
        crystal_system=analysis.crystal_system,
        space_group=analysis.space_group,
        confidence_score=analysis.confidence_score,
        crystallite_size_nm=analysis.crystallite_size_nm,
        mean_peak_shift_deg=analysis.mean_peak_shift_deg,
        strain_indicator=analysis.strain_indicator,
        detected_phases=analysis.detected_phases,
        peaks=peaks_out,
        matched_peaks=matched_peaks_out,
        graph_experimental=graph_paths.experimental,
        graph_standard=graph_paths.standard,
        graph_overlay=graph_paths.overlay,
        report_pdf=pdf_path,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/{file_id}",
    response_model=AnalysisResponse,
    summary="Run XRD analysis pipeline",
    description="Runs all 10 pipeline stages for the uploaded file and returns full results.",
)
async def run_analysis(file_id: str):
    """Trigger the full XRD analysis pipeline for a given file_id."""
    record = file_handler.get_upload_record(file_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No uploaded file found for file_id '{file_id}'.",
        )

    file_path = record["file_path"]
    if not Path(file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Uploaded file no longer exists on disk.",
        )

    try:
        result = _run_pipeline(file_id, file_path)
    except CSVReadError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Pipeline failed for file_id=%s", file_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {exc}",
        )

    return result


@router.get(
    "/{file_id}",
    response_model=AnalysisResponse,
    summary="Get stored analysis results",
)
async def get_analysis(file_id: str):
    """Return previously computed analysis results for a file_id."""
    result = file_handler.get_analysis_result(file_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis found for file_id '{file_id}'. Run POST first.",
        )

    # Fetch peaks from the peaks table
    peaks_raw = file_handler.get_peaks(file_id)
    peaks_out = [
        PeakRow(
            two_theta=round(float(p["two_theta"]), 4),
            intensity=round(float(p["intensity"]), 2),
            fwhm_deg=round(float(p.get("fwhm_deg") or 0), 4),
            prominence=round(float(p.get("prominence") or 0), 2),
        )
        for p in peaks_raw
    ]

    # matched_peaks are not stored separately — return empty list on GET
    # (full matched_peaks are available via POST which re-runs the pipeline)
    return AnalysisResponse(
        file_id=file_id,
        status="done",
        compound_name=result.get("compound_name") or "",
        formula=result.get("formula") or "",
        crystal_system=result.get("crystal_system") or "",
        space_group=result.get("space_group") or "",
        confidence_score=float(result.get("confidence_score") or 0),
        crystallite_size_nm=float(result.get("crystallite_size_nm") or 0),
        mean_peak_shift_deg=float(result.get("mean_peak_shift_deg") or 0),
        strain_indicator=str(result.get("strain_indicator") or ""),
        detected_phases=result.get("detected_phases") or [],
        peaks=peaks_out,
        matched_peaks=[],
        graph_experimental=result.get("graph_experimental") or "",
        graph_standard=result.get("graph_standard") or "",
        graph_overlay=result.get("graph_overlay") or "",
        report_pdf=result.get("report_pdf") or "",
    )

@router.get(
    "/compounds",
    summary="List all standard compounds",
)
async def list_compounds():
    """Return a list of all compound names and formulas in the standards database."""
    matcher = PeakMatcher()
    compounds = [
        {"compound_name": s.get("compound_name"), "formula": s.get("formula")}
        for s in matcher._standards
    ]
    return {"total": len(compounds), "compounds": compounds}