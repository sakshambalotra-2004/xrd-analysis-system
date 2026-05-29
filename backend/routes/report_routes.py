"""
routes/report_routes.py
========================
Report Routes — REST endpoints for downloading generated reports.

Endpoints
---------
GET /api/report/{file_id}
    Download the PDF report for a completed analysis.

GET /api/report/{file_id}/graphs
    Return URLs to all generated graph images for a file_id.

GET /api/report/{file_id}/summary
    Return a lightweight JSON summary without graph/PDF paths.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from config import settings
from utils.file_handler import FileHandler

logger = logging.getLogger(__name__)
router = APIRouter()
file_handler = FileHandler()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/{file_id}",
    response_class=FileResponse,
    summary="Download PDF report",
    description="Streams the generated PDF report for a completed analysis run.",
)
async def download_report(file_id: str):
    """Return the PDF report as a file download."""
    result = file_handler.get_analysis_result(file_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis found for file_id '{file_id}'.",
        )

    pdf_path = result.get("report_pdf", "")
    if not pdf_path or not Path(pdf_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF report file not found on disk.",
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"xrd_report_{file_id}.pdf",
    )


@router.get(
    "/{file_id}/graphs",
    summary="Get graph image URLs",
)
async def get_graphs(file_id: str):
    """Return public URLs to the experimental, standard, and overlay graph images."""
    result = file_handler.get_analysis_result(file_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis found for file_id '{file_id}'.",
        )

    def to_url(abs_path: str) -> str | None:
        if not abs_path:
            return None
        # Convert absolute filesystem path to a URL relative to /reports static mount
        try:
            rel = Path(abs_path).relative_to(settings.REPORTS_BASE_DIR)
            return f"/reports/{rel.as_posix()}"
        except ValueError:
            return None

    return {
        "file_id": file_id,
        "experimental": to_url(result.get("graph_experimental", "")),
        "standard":     to_url(result.get("graph_standard", "")),
        "overlay":      to_url(result.get("graph_overlay", "")),
    }


@router.get(
    "/{file_id}/summary",
    summary="Get analysis summary (no file paths)",
)
async def get_summary(file_id: str):
    """Return a lightweight JSON summary of the analysis results."""
    result = file_handler.get_analysis_result(file_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis found for file_id '{file_id}'.",
        )

    return {
        "file_id":            file_id,
        "compound_name":      result.get("compound_name"),
        "formula":            result.get("formula"),
        "crystal_system":     result.get("crystal_system"),
        "space_group":        result.get("space_group"),
        "confidence_score":   result.get("confidence_score"),
        "crystallite_size_nm":result.get("crystallite_size_nm"),
        "mean_peak_shift_deg":result.get("mean_peak_shift_deg"),
        "strain_indicator":   result.get("strain_indicator"),
        "detected_phases":    result.get("detected_phases"),
    }