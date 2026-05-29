"""
routes/upload_routes.py
========================
Upload Routes — REST endpoints for receiving XRD CSV files.

Endpoints
---------
POST /api/upload/csv
    Accept a multipart CSV file, validate it, persist it to disk and the
    SQLite database, and return a unique file_id for subsequent analysis calls.

GET /api/upload/status/{file_id}
    Return upload metadata and processing status for a given file_id.

DELETE /api/upload/{file_id}
    Remove an uploaded file and its database record.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import settings
from services.csv_reader import CSVReadError, CSVReader
from utils.file_handler import FileHandler

logger = logging.getLogger(__name__)
router = APIRouter()

csv_reader = CSVReader()
file_handler = FileHandler()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    file_id: str
    filename: str
    rows: int
    two_theta_min: float
    two_theta_max: float
    uploaded_at: str
    message: str


class UploadStatusResponse(BaseModel):
    file_id: str
    filename: str
    status: str          # "uploaded" | "processing" | "done" | "error"
    uploaded_at: str
    file_path: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/csv",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an XRD CSV file",
    description=(
        "Upload a CSV file containing 2θ (two-theta) and intensity columns. "
        "Returns a `file_id` used to trigger analysis."
    ),
)
async def upload_csv(file: UploadFile = File(...)):
    """
    Accept and validate an XRD CSV file.

    - Validates MIME type and file extension
    - Checks file size against ``settings.UPLOAD_MAX_SIZE_MB``
    - Parses the CSV to confirm required columns exist
    - Persists the file and records metadata in SQLite
    """
    # ---- extension check ----
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{suffix}' not supported. Allowed: {settings.ALLOWED_EXTENSIONS}",
        )

    # ---- read bytes ----
    content = await file.read()
    if len(content) > settings.upload_max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.UPLOAD_MAX_SIZE_MB} MB.",
        )

    # ---- validate CSV structure ----
    try:
        df = csv_reader.load_bytes(content, filename=file.filename or "upload.csv")
    except CSVReadError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    # ---- persist file ----
    file_id = str(uuid.uuid4())
    save_path = Path(settings.UPLOAD_CSV_DIR) / f"{file_id}{suffix}"
    save_path.write_bytes(content)

    # ---- record in SQLite ----
    uploaded_at = datetime.utcnow().isoformat()
    file_handler.record_upload(
        file_id=file_id,
        filename=file.filename or "upload.csv",
        file_path=str(save_path),
        rows=len(df),
        uploaded_at=uploaded_at,
    )

    logger.info("Uploaded '%s' → file_id=%s (%d rows)", file.filename, file_id, len(df))

    return UploadResponse(
        file_id=file_id,
        filename=file.filename or "upload.csv",
        rows=len(df),
        two_theta_min=round(float(df["two_theta"].min()), 4),
        two_theta_max=round(float(df["two_theta"].max()), 4),
        uploaded_at=uploaded_at,
        message="File uploaded and validated successfully.",
    )


@router.get(
    "/status/{file_id}",
    response_model=UploadStatusResponse,
    summary="Get upload status",
)
async def get_upload_status(file_id: str):
    """Return metadata and processing status for a previously uploaded file."""
    record = file_handler.get_upload_record(file_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No upload found for file_id '{file_id}'.",
        )
    return UploadStatusResponse(**record)


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an uploaded file",
)
async def delete_upload(file_id: str):
    """Remove an uploaded CSV and its database record."""
    record = file_handler.get_upload_record(file_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No upload found for file_id '{file_id}'.",
        )

    # Delete the file from disk
    file_path = Path(record["file_path"])
    if file_path.exists():
        file_path.unlink()

    file_handler.delete_upload_record(file_id)
    logger.info("Deleted upload file_id=%s", file_id)

    return JSONResponse(content={"message": f"Upload '{file_id}' deleted successfully."})