"""
utils/validation.py
====================
Input validation helpers for the XRD Analysis System.

Provides reusable validators for file uploads, DataFrame structure,
peak data, and configuration ranges — keeping validation logic
out of routes and services.
"""

import re
from pathlib import Path
from typing import Any

import pandas as pd

from config import settings
from utils.constants import TWO_THETA_MAX_DEG, TWO_THETA_MIN_DEG


class ValidationError(ValueError):
    """Raised when input fails a validation check."""


# ---------------------------------------------------------------------------
# File validation
# ---------------------------------------------------------------------------

def validate_file_extension(filename: str) -> None:
    """Raise ValidationError if the file extension is not in ALLOWED_EXTENSIONS."""
    suffix = Path(filename).suffix.lower()
    if suffix not in settings.ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File extension '{suffix}' is not allowed. "
            f"Accepted extensions: {settings.ALLOWED_EXTENSIONS}"
        )


def validate_file_size(content: bytes) -> None:
    """Raise ValidationError if the file exceeds the configured maximum size."""
    if len(content) > settings.upload_max_bytes:
        raise ValidationError(
            f"File size {len(content) / 1024 / 1024:.2f} MB exceeds the "
            f"maximum allowed size of {settings.UPLOAD_MAX_SIZE_MB} MB."
        )


def validate_file_id(file_id: str) -> None:
    """Raise ValidationError if the file_id is not a valid UUID v4 string."""
    uuid4_re = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )
    if not uuid4_re.match(file_id):
        raise ValidationError(f"Invalid file_id format: '{file_id}'. Expected UUID v4.")


# ---------------------------------------------------------------------------
# DataFrame validation
# ---------------------------------------------------------------------------

def validate_xrd_dataframe(df: pd.DataFrame) -> None:
    """
    Validate that a DataFrame has the expected XRD columns and sensible values.

    Raises
    ------
    ValidationError
    """
    required = {"two_theta", "intensity"}
    missing = required - set(df.columns)
    if missing:
        raise ValidationError(f"DataFrame is missing required columns: {missing}")

    if df.empty:
        raise ValidationError("DataFrame is empty — no data rows found.")

    if len(df) < 5:
        raise ValidationError(
            f"Too few data rows ({len(df)}). At least 5 rows are required."
        )

    out_of_range = df[
        (df["two_theta"] < TWO_THETA_MIN_DEG) | (df["two_theta"] > TWO_THETA_MAX_DEG)
    ]
    if not out_of_range.empty:
        raise ValidationError(
            f"{len(out_of_range)} rows have 2θ values outside the valid range "
            f"[{TWO_THETA_MIN_DEG}°, {TWO_THETA_MAX_DEG}°]."
        )

    if (df["intensity"] < 0).any():
        raise ValidationError("Negative intensity values detected in DataFrame.")


def validate_peaks_dataframe(peaks_df: pd.DataFrame) -> None:
    """Validate the output of PeakDetector.detect()."""
    if peaks_df.empty:
        return  # Empty result is acceptable (no peaks found)

    required = {"two_theta", "intensity"}
    missing = required - set(peaks_df.columns)
    if missing:
        raise ValidationError(f"Peaks DataFrame missing columns: {missing}")


# ---------------------------------------------------------------------------
# Configuration value validation
# ---------------------------------------------------------------------------

def validate_tolerance(tolerance: float) -> None:
    """Raise if peak matching tolerance is outside a physically reasonable range."""
    if not (0.01 <= tolerance <= 2.0):
        raise ValidationError(
            f"Peak matching tolerance {tolerance}° is outside the acceptable "
            "range [0.01°, 2.0°]."
        )


def validate_wavelength(wavelength_A: float) -> None:
    """Raise if the X-ray wavelength is outside a reasonable laboratory range."""
    if not (0.5 <= wavelength_A <= 3.0):
        raise ValidationError(
            f"Wavelength {wavelength_A} Å is outside the typical laboratory "
            "range [0.5, 3.0] Å."
        )


def validate_scherrer_k(k: float) -> None:
    """Raise if the Scherrer shape factor K is outside [0.5, 1.5]."""
    if not (0.5 <= k <= 1.5):
        raise ValidationError(
            f"Scherrer constant K={k} is outside the physically reasonable "
            "range [0.5, 1.5]."
        )


# ---------------------------------------------------------------------------
# Standard compound JSON validation
# ---------------------------------------------------------------------------

def validate_standard_compound(data: dict[str, Any]) -> None:
    """
    Validate the structure of a standard compound JSON dictionary.

    Parameters
    ----------
    data : dict
        Parsed JSON object from a standards file.

    Raises
    ------
    ValidationError
    """
    required_fields = ["compound_name", "formula", "crystal_system", "space_group", "peaks"]
    for field_name in required_fields:
        if field_name not in data:
            raise ValidationError(
                f"Standard compound JSON is missing required field '{field_name}'."
            )

    if not isinstance(data["peaks"], list) or len(data["peaks"]) == 0:
        raise ValidationError(
            f"Standard compound '{data.get('compound_name')}' has no peaks defined."
        )

    for i, peak in enumerate(data["peaks"]):
        for key in ("two_theta", "d", "intensity"):
            if key not in peak:
                raise ValidationError(
                    f"Peak #{i} in '{data.get('compound_name')}' is missing field '{key}'."
                )
        t = peak["two_theta"]
        if not (TWO_THETA_MIN_DEG < t < TWO_THETA_MAX_DEG):
            raise ValidationError(
                f"Peak #{i} two_theta={t}° is outside valid range in "
                f"'{data.get('compound_name')}'."
            )