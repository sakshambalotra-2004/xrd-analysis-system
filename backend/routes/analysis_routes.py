"""
routes/analysis_routes.py
==========================
Analysis Routes — REST endpoints that trigger and retrieve XRD analysis.
Fully synchronized to explicitly map and serialize polytype properties.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel

from config import settings
from services.origin_exporter import OriginExporter
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
origin_exporter = OriginExporter()


# ---------------------------------------------------------------------------
# Request & Response Pydantic models
# ---------------------------------------------------------------------------

class AnalysisRequest(BaseModel):
    file_id: str


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
    phase_name: str
    polytype: str


class AnalysisResponse(BaseModel):
    file_id: str
    status: str
    compound_name: str
    formula: str
    polytype: str = ""  # FIXED: Default value prevents future ValidationErrors
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
    origin_project: str
    full_two_theta: list[float]
    full_intensity: list[float]


# ---------------------------------------------------------------------------
# Core Pipeline Execution
# ---------------------------------------------------------------------------

def _run_pipeline(file_id: str, file_path: str) -> AnalysisResponse:
    """Execute the full 10-stage XRD analysis pipeline with fail-safe fallbacks."""
    logger.info("Starting analysis pipeline execution for file_id=%s", file_id)

    # Core mathematical processing stages
    df = csv_reader.load(file_path)
    df_smooth = noise_filter.filter(df)
    peaks_df = peak_detector.detect(df_smooth)
    
    candidates = peak_matcher.match(peaks_df)
    best_match = candidates[0] if candidates else None

    # Check for valid crystalline match entries
    is_crystalline_match = False
    if best_match:
        confidence = float(getattr(best_match, "similarity_score", getattr(best_match, "confidence_score", 0.0)))
        if confidence >= settings.MIN_SIMILARITY_SCORE:
            is_crystalline_match = True

    if not is_crystalline_match:
        logger.info("Sample file_id=%s determined to be Amorphous / Background Matrix.", file_id)
        best_match = None

    # Structural math analysis stage
    analysis = crystal_analyzer.analyze(peaks_df, best_match, all_matches=candidates if is_crystalline_match else [])

    # Extract polytype parameter cleanly to feed the response instantiation block
    detected_polytype = str(getattr(best_match, "polytype", "")) if best_match else ""

    # =========================================================================
# VISUAL & REPORTING ASSETS (Fail-Safe Non-Blocking Wrappers)
# =========================================================================
    try:
        graph_paths = graph_generator.generate_all(df_smooth, peaks_df, best_match, file_id)
    except Exception as graph_exc:
        logger.error("Visual graph rendering bypassed due to an internal exception: %s", graph_exc)
        class EmptyGraphPaths:
            experimental = ""
            standard = ""
            overlay = ""
        graph_paths = EmptyGraphPaths()

    try:
        # UPGRADE: Grab the top confident matches (up to 3) so the PDF loops through all polytypes!
        top_matches = candidates[:3] if is_crystalline_match and candidates else None
        
        pdf_path = report_generator.generate(
            file_id=file_id, 
            analysis=analysis, 
            peaks_df=peaks_df, 
            graph_paths=graph_paths, 
            best_match=top_matches # Passing the list here triggers the multi-table loop
        )
    except Exception as pdf_exc:
        logger.error("PDF document generation bypassed due to an internal exception: %s", pdf_exc)
        pdf_path = ""

    try:
        origin_results = origin_exporter.export_project_and_plots(file_id, df_smooth, peaks_df, best_match)
        opju_path = str(origin_results.get("project_path", "")) if isinstance(origin_results, dict) else str(getattr(origin_results, "project_path", ""))
    except Exception as origin_exc:
        logger.warning("Origin Project export bypassed due to an internal exception: %s", origin_exc)
        opju_path = ""
    # =========================================================================
    # PERSISTENCE LAYER SYNCHRONIZATION
    # =========================================================================
    file_handler.save_analysis_result(file_id, analysis, pdf_path)
    
    # Store detected peak arrays
    peaks_list = []
    for _, r in peaks_df.iterrows():
        peaks_list.append({
            "two_theta": round(float(r.get("two_theta", r.iloc[0] if len(r) > 0 else 0.0)), 4),
            "intensity": round(float(r.get("intensity", r.iloc[1] if len(r) > 1 else 0.0)), 2),
            "fwhm_deg": round(float(r.get("fwhm_deg", 0.0)), 4),
            "prominence": round(float(r.get("prominence", 0.0)), 2),
        })
    file_handler.save_peaks(file_id, peaks_list)

    # Store matched reference peaks
    matched_peaks_out: list[MatchedPeakRow] = []
    all_saved_matches = []

    if is_crystalline_match and candidates:
        for candidate in candidates:
            # We filter by your existing minimum similarity threshold
            if candidate.similarity_score >= settings.MIN_SIMILARITY_SCORE:
                for mp in getattr(candidate, "matched_peaks", []):
                    all_saved_matches.append({
                        "two_theta_exp": float(getattr(mp, "two_theta_exp", 0.0)),
                        "two_theta_std": float(getattr(mp, "two_theta_std", 0.0)),
                        "delta_two_theta": float(getattr(mp, "delta_two_theta", 0.0)),
                        "d_spacing": float(getattr(mp, "d_spacing", 0.0)),
                        "intensity_std": float(getattr(mp, "intensity_std", 0.0)),
                        "h": int(getattr(mp, "h", 0)),
                        "k": int(getattr(mp, "k", 0)),
                        "l": int(getattr(mp, "l", 0)),
                        "phase_name": str(getattr(mp, "phase_name", getattr(candidate, "compound_name", "Unknown"))),
                        "polytype": str(getattr(mp, "polytype", getattr(candidate, "polytype", "")))
                    })
        
        file_handler.save_matched_peaks(file_id, all_saved_matches)
        
        for sm in all_saved_matches:
            matched_peaks_out.append(MatchedPeakRow(**sm))
    else:
        file_handler.save_matched_peaks(file_id, [])

    peaks_out = [PeakRow(**p) for p in peaks_list]

    # Resolve alignment column headers safely
    angle_col = 'two_theta' if 'two_theta' in df_smooth.columns else ('Angle' if 'Angle' in df_smooth.columns else df_smooth.columns[0])
    intensity_col = 'intensity' if 'intensity' in df_smooth.columns else ('Intensity' if 'Intensity' in df_smooth.columns else df_smooth.columns[1])

    return AnalysisResponse(
        file_id=file_id,
        status="done",
        compound_name=str(getattr(analysis, "primary_compound", "No Crystalline Match Found")),
        formula=str(getattr(analysis, "formula", "N/A")),
        polytype=detected_polytype,  # FIXED: Explicitly mapped here
        crystal_system=str(getattr(analysis, "crystal_system", "Disordered / Amorphous")),
        space_group=str(getattr(analysis, "space_group", "N/A")),
        confidence_score=float(getattr(analysis, "confidence_score", 0.0)),
        crystallite_size_nm=float(getattr(analysis, "crystallite_size_nm", 0.0)),
        mean_peak_shift_deg=float(getattr(analysis, "mean_peak_shift_deg", 0.0)),
        strain_indicator=str(getattr(analysis, "strain_indicator", "N/A")),
        detected_phases=list(getattr(analysis, "detected_phases", ["Amorphous Background Matrix"])),
        peaks=peaks_out,
        matched_peaks=matched_peaks_out,
        graph_experimental=str(getattr(graph_paths, "experimental", "")),
        graph_standard=str(getattr(graph_paths, "standard", "")),
        graph_overlay=str(getattr(graph_paths, "overlay", "")),
        report_pdf=str(pdf_path),
        origin_project=str(opju_path),
        full_two_theta=df_smooth[angle_col].astype(float).tolist(),
        full_intensity=df_smooth[intensity_col].astype(float).tolist(),
    )


# ---------------------------------------------------------------------------
# REST Endpoints
# ---------------------------------------------------------------------------

@router.get("/history/recent", summary="Get recent analyses for the dashboard")
async def get_recent_history(limit: int = 5):
    """Returns the most recent analysis runs directly from the SQLite database."""
    records = file_handler.get_recent_analyses(limit)
    
    # Clean up the stringified database columns before sending to React
    for r in records:
        raw_phases = r.get("detected_phases")
        if isinstance(raw_phases, str):
            r["detected_phases"] = [p.strip() for p in raw_phases.split(",") if p.strip()]
        else:
            r["detected_phases"] = []
            
    return {"history": records}


@router.post("/{file_id}", response_model=AnalysisResponse, summary="Run XRD pipeline (Path style)")
async def run_analysis_path(file_id: str):
    record = file_handler.get_upload_record(file_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"No uploaded file found for file_id '{file_id}'.")
    return _run_pipeline(file_id, record["file_path"])


@router.post("", response_model=AnalysisResponse, summary="Run XRD pipeline (JSON body style)")
async def run_analysis_body(req: AnalysisRequest):
    record = file_handler.get_upload_record(req.file_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"No uploaded file found for file_id '{req.file_id}'.")
    return _run_pipeline(req.file_id, record["file_path"])


@router.get("/{file_id}", response_model=AnalysisResponse, summary="Get stored analysis results")
async def get_analysis(file_id: str):
    """Return previously computed analysis results safely from history."""
    result = file_handler.get_analysis_result(file_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"No analysis found for file_id '{file_id}'.")

    peaks_raw = file_handler.get_peaks(file_id) or []
    peaks_out = [
        PeakRow(
            two_theta=round(float(p.get("two_theta", 0.0)), 4),
            intensity=round(float(p.get("intensity", 0.0)), 2),
            fwhm_deg=round(float(p.get("fwhm_deg", 0.0)), 4),
            prominence=round(float(p.get("prominence", 0.0)), 2),
        )
        for p in peaks_raw
    ]

    matched_raw = file_handler.get_matched_peaks(file_id) or []
    matched_peaks_out = [
        MatchedPeakRow(
            two_theta_exp=round(float(m.get("two_theta_exp", 0.0)), 4),
            two_theta_std=round(float(m.get("two_theta_std", 0.0)), 4),
            delta_two_theta=round(float(m.get("delta_two_theta", 0.0)), 4),
            d_spacing=round(float(m.get("d_spacing", 0.0)), 4),
            intensity_std=round(float(m.get("intensity_std", 0.0)), 2),
            h=int(m.get("h", 0)), k=int(m.get("k", 0)), l=int(m.get("l", 0)),
            phase_name=str(m.get("phase_name", result.get("compound_name", "Unknown"))),
            polytype=str(m.get("polytype", result.get("polytype", "")))
        )
        for m in matched_raw
    ]

    raw_phases = result.get("detected_phases") or ["Amorphous Background Matrix"]
    if isinstance(raw_phases, str):
        raw_phases = [p.strip() for p in raw_phases.split(",") if p.strip()]

    project_dir = Path(settings.REPORTS_BASE_DIR) / "origin_files"
    opju_file_path = project_dir / f"xrd_analysis_{file_id}.opju"
    origin_project_status = str(opju_file_path) if opju_file_path.exists() else ""

    record = file_handler.get_upload_record(file_id)
    x_pts, y_pts = [], []
    if record and Path(record["file_path"]).exists():
        try:
            df_smooth = noise_filter.filter(csv_reader.load(record["file_path"]))
            angle_col = 'two_theta' if 'two_theta' in df_smooth.columns else ('Angle' if 'Angle' in df_smooth.columns else df_smooth.columns[0])
            intensity_col = 'intensity' if 'intensity' in df_smooth.columns else ('Intensity' if 'Intensity' in df_smooth.columns else df_smooth.columns[1])
            x_pts = df_smooth[angle_col].astype(float).tolist()
            y_pts = df_smooth[intensity_col].astype(float).tolist()
        except:
            pass

    return AnalysisResponse(
        file_id=file_id,
        status="done",
        compound_name=str(result.get("compound_name", "No Crystalline Match Found")),
        formula=str(result.get("formula", "N/A")),
        polytype=str(result.get("polytype", "")),
        crystal_system=str(result.get("crystal_system", "Disordered / Amorphous")),
        space_group=str(result.get("space_group", "N/A")),
        confidence_score=float(result.get("confidence_score", 0.0)),
        crystallite_size_nm=float(result.get("crystallite_size_nm", 0.0)),
        mean_peak_shift_deg=float(result.get("mean_peak_shift_deg", 0.0)),
        strain_indicator=str(result.get("strain_indicator", "N/A")),
        detected_phases=list(raw_phases),
        peaks=peaks_out,
        matched_peaks=matched_peaks_out,
        graph_experimental=str(result.get("graph_experimental", "")),
        graph_standard=str(result.get("graph_standard", "")),
        graph_overlay=str(result.get("graph_overlay", "")),
        report_pdf=str(result.get("report_pdf", "")),
        origin_project=origin_project_status,
        full_two_theta=x_pts,
        full_intensity=y_pts,
    )



@router.delete("/{file_id}", summary="Delete an analysis record")
async def delete_analysis(file_id: str):
    """Deletes an analysis record, its database peaks, and all physical files."""
    record = file_handler.get_upload_record(file_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"No analysis found for '{file_id}'.")
    
    # 1. Delete from SQLite (cascades to all other tables)
    file_handler.delete_upload_record(file_id)
    
    # 2. Delete all physical files from the disk to free up space
    try:
        from pathlib import Path
        
        # Build a list of all potential files generated by this file_id
        reports_dir = Path(settings.REPORTS_BASE_DIR)
        files_to_delete = [
            Path(record["file_path"]), # The original CSV upload
            reports_dir / "pdf_reports" / f"{file_id}_report.pdf",
            reports_dir / "graphs" / f"{file_id}_experimental.png",
            reports_dir / "graphs" / f"{file_id}_standard.png",
            reports_dir / "graphs" / f"{file_id}_overlay.png",
            reports_dir / "origin_files" / f"xrd_analysis_{file_id}.opju",
            reports_dir / "origin_images" / f"xrd_overlay_{file_id}.png",
        ]
        
        # Loop through and safely delete them if they exist
        for file_path in files_to_delete:
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                logger.info("Deleted physical file: %s", file_path.name)
                
    except Exception as e:
        logger.error("Error during physical file cleanup for %s: %s", file_id, e)

    return {"status": "deleted", "file_id": file_id}