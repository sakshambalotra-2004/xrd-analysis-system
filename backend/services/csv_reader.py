"""
services/csv_reader.py
======================
CSV Reader Module — Stage 1 of the XRD analysis pipeline.

Responsibilities:
  - Accept a file path or raw bytes of an uploaded CSV
  - Validate column presence and data types
  - Normalise column names (strip whitespace, lowercase)
  - Return a clean pandas DataFrame ready for noise filtering

Expected CSV columns (case-insensitive, flexible naming):
  - Two-theta angle  : "2theta", "2theta (°)", "angle", "°2theta"
  - Intensity        : "intensity", "counts", "i"

Usage:
    from services.csv_reader import CSVReader

    reader = CSVReader()
    df = reader.load("/uploads/csv/sample.csv")
    # df.columns → ["two_theta", "intensity"]
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from config import settings

logger = logging.getLogger(__name__)

# Column name aliases accepted as 2θ input
TWO_THETA_ALIASES = {"2theta", "2theta (°)", "angle", "°2theta", "two_theta", "2th"}

# Column name aliases accepted as intensity input
INTENSITY_ALIASES = {"intensity", "counts", "i", "int", "cps", "intensity (a.u.)"}


class CSVReadError(ValueError):
    """Raised when the CSV cannot be parsed or validated."""


class CSVReader:
    """Loads and validates XRD CSV files into a standardised DataFrame."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, filepath: str | Path) -> pd.DataFrame:
        """
        Read an XRD CSV file and return a clean DataFrame.

        Parameters
        ----------
        filepath : str | Path
            Absolute or relative path to the .csv file.

        Returns
        -------
        pd.DataFrame
            Columns: ['two_theta', 'intensity'] — both float64, sorted by
            two_theta ascending, with NaN rows dropped.

        Raises
        ------
        CSVReadError
            If the file cannot be read, required columns are missing, or
            fewer than 5 valid data rows remain after cleaning.
        """
        filepath = Path(filepath)
        logger.info("Loading CSV: %s", filepath)

        raw = self._read_raw(filepath)
        df = self._normalise_columns(raw)
        df = self._clean(df)
        self._validate(df)

        logger.info(
            "CSV loaded successfully — %d rows, 2θ range %.3f°–%.3f°",
            len(df),
            df["two_theta"].min(),
            df["two_theta"].max(),
        )
        return df

    def load_bytes(self, content: bytes, filename: str = "upload.csv") -> pd.DataFrame:
        """
        Parse CSV from raw bytes (e.g. from an HTTP upload).

        Parameters
        ----------
        content : bytes
            Raw file bytes.
        filename : str
            Original filename, used only for logging.

        Returns
        -------
        pd.DataFrame
            Same contract as :meth:`load`.
        """
        import io

        logger.info("Parsing CSV bytes for file: %s", filename)
        try:
            raw = pd.read_csv(io.BytesIO(content))
        except Exception as exc:
            raise CSVReadError(f"Failed to parse CSV bytes: {exc}") from exc

        df = self._normalise_columns(raw)
        df = self._clean(df)
        self._validate(df)
        return df

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _read_raw(self, filepath: Path) -> pd.DataFrame:
        """Attempt to read the CSV, trying common delimiters."""
        if not filepath.exists():
            raise CSVReadError(f"File not found: {filepath}")

        for sep in (",", ";", "\t", " "):
            try:
                df = pd.read_csv(filepath, sep=sep, engine="python", skip_blank_lines=True)
                if df.shape[1] >= 2:
                    return df
            except Exception:
                continue

        raise CSVReadError(
            f"Could not parse '{filepath.name}' with any supported delimiter "
            "(comma, semicolon, tab, space)."
        )

    def _normalise_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map flexible column names → 'two_theta', 'intensity'."""
        mapping: dict[str, str] = {}
        for col in df.columns:
            normalised = col.strip().lower().replace(" ", "_").replace("(", "").replace(")", "").replace("°", "")
            if normalised in TWO_THETA_ALIASES or col.strip().lower() in TWO_THETA_ALIASES:
                mapping[col] = "two_theta"
            elif normalised in INTENSITY_ALIASES or col.strip().lower() in INTENSITY_ALIASES:
                mapping[col] = "intensity"

        if "two_theta" not in mapping.values():
            raise CSVReadError(
                f"No 2θ column found. Expected one of: {sorted(TWO_THETA_ALIASES)}. "
                f"Got: {list(df.columns)}"
            )
        if "intensity" not in mapping.values():
            raise CSVReadError(
                f"No intensity column found. Expected one of: {sorted(INTENSITY_ALIASES)}. "
                f"Got: {list(df.columns)}"
            )

        df = df.rename(columns=mapping)[["two_theta", "intensity"]]
        return df

    def _clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Coerce types, drop NaN/negative rows, sort by 2θ."""
        df = df.copy()
        df["two_theta"] = pd.to_numeric(df["two_theta"], errors="coerce")
        df["intensity"] = pd.to_numeric(df["intensity"], errors="coerce")
        df = df.dropna(subset=["two_theta", "intensity"])
        df = df[df["intensity"] >= 0]           # drop unphysical negative counts
        df = df[df["two_theta"].between(0, 180)] # physical 2θ range
        df = df.sort_values("two_theta").reset_index(drop=True)
        df["intensity"] = df["intensity"].astype(np.float64)
        df["two_theta"] = df["two_theta"].astype(np.float64)
        return df

    def _validate(self, df: pd.DataFrame) -> None:
        """Raise if the cleaned DataFrame has too few rows."""
        if len(df) < 5:
            raise CSVReadError(
                f"Only {len(df)} valid data rows remain after cleaning. "
                "Minimum required is 5."
            )