"""
routes/report_routes.py
========================
Report Routes — REST endpoints for downloading generated reports and images.
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

@router.get("/{file_id}", response_class=FileResponse, summary="Download PDF report")
async def download_report(file_id: str):
    result = file_handler.get_analysis_result(file_id)
    if not result:
        raise HTTPException(status_code=404, detail="No analysis found.")
    pdf_path = result.get("report_pdf", "")
    if not pdf_path or not Path(pdf_path).exists():
        raise HTTPException(status_code=404, detail="PDF report file not found on disk.")
    return FileResponse(path=pdf_path, media_type="application/pdf", filename=f"xrd_report_{file_id}.pdf")

@router.get("/{file_id}/origin", response_class=FileResponse, summary="Download automated Origin Project (.opju)")
async def download_origin_project(file_id: str):
    """Streams the compiled native workspace file asset down to client node environments."""
    project_dir = Path(settings.REPORTS_ORIGIN_FILES_DIR)
    opju_path = project_dir / f"xrd_analysis_{file_id}.opju"

    if not opju_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Origin project workspace binary asset not found on local storage node.",
        )
    return FileResponse(path=str(opju_path), media_type="application/octet-stream", filename=f"xrd_analysis_{file_id}.opju")

@router.get("/{file_id}/origin-image", response_class=FileResponse, summary="Get automated high-resolution Origin chart image")
async def get_origin_chart_image(file_id: str):
    """
    Locates and serves the XRD overlay chart image for a given file_id.
    Recursively scans the entire reports directory to find any image containing 
    the file_id to guarantee successful retrieval regardless of naming variations.
    """
    reports_base = Path(settings.REPORTS_BASE_DIR)

    # 1. Prioritize the high-fidelity automated Origin-style image layout
    preferred_origin_path = Path(settings.REPORTS_ORIGIN_IMAGES_DIR) / f"xrd_overlay_{file_id}.png"
    if preferred_origin_path.exists():
        return FileResponse(path=str(preferred_origin_path), media_type="image/png")
        
    # 2. DYNAMIC AUTODISCOVERY: Recursively scan the entire reports directory
    # for ANY PNG file containing the unique file_id token string in its filename.
    if reports_base.exists():
        for img_path in reports_base.rglob(f"*{file_id}*.png"):
            if img_path.is_file():
                logger.info("Autodiscovery Success -> Located matching chart at: %s", img_path)
                return FileResponse(path=str(img_path), media_type="image/png")
            
    # 3. GENERIC PLATFORM FALLBACK: Look for standard generic pipeline output charts 
    # that might be sharing a global folder context without a UUID string signature
    generic_fallbacks = [
        reports_base / "graphs" / f"overlay_{file_id}.png",
        reports_base / "overlay_images" / f"overlay_{file_id}.png",
        reports_base / "xrd_plot_detailed.png",
        reports_base / "xrd_plot.png",
    ]
    
    for path in generic_fallbacks:
        if path.exists() and path.is_file():
            logger.info("Generic Fallback Success -> Serving: %s", path)
            return FileResponse(path=str(path), media_type="image/png")
            
    # 4. Raise 404 explicitly if no graph matches are found on storage
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"XRD overlay chart image resource could not be located on disk for file_id '{file_id}'."
    )