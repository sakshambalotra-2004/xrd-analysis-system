"""
services/csv_reader.py
======================
CSV Reader Module — Stage 1 of the XRD analysis pipeline.

Responsibilities:
  - Accept a file path or raw bytes of an uploaded CSV
  - Extract instrument metadata (Scan Axis, Fixed Angles) for HRXRD/Omega Scans
  - Validate column presence and data types (maintaining 6-decimal precision)
  - Normalise column names (strip whitespace, lowercase)
  - Handle PANalytical XPERT-PRO exports with metadata header blocks
  - Return a clean pandas DataFrame ready for noise filtering

Expected CSV columns (case-insensitive, flexible naming):
  - Two-theta / Omega angle : "2theta", "angle", "two_theta", "omega"
  - Intensity               : "intensity", "counts", "i"
"""

import io
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Column name aliases accepted as the primary X-axis input
# UPGRADE: Added "omega" and "rel_angle" to support Rocking Curves
TWO_THETA_ALIASES = {"2theta", "2theta (°)", "angle", "°2theta", "two_theta", "2th", "omega", "rel_angle"}

# Column name aliases accepted as intensity input
INTENSITY_ALIASES = {"intensity", "counts", "i", "int", "cps", "intensity (a.u.)"}


class CSVReadError(ValueError):
    """Raised when the CSV cannot be parsed or validated."""


class CSVReader:
    """Loads and validates XRD CSV files into a standardised DataFrame."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_metadata(self, content_or_path: str | Path | bytes) -> dict:
        """
        Extract PANalytical instrument metadata headers before parsing the data.
        This is crucial for identifying High-Resolution Rocking Curves (Omega Scans).
        """
        metadata = {
            "scan_axis": "2Theta", # Default to standard powder XRD
            "fixed_2theta": None, 
            "fixed_omega": None
        }
        lines = []

        try:
            if isinstance(content_or_path, bytes):
                text = content_or_path.decode("utf-8", errors="replace")
                lines = text.splitlines()[:60]
            else:
                with open(content_or_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = [f.readline().strip() for _ in range(60)]

            for line in lines:
                clean_line = line.strip()
                
                # Check for Omega Scan Type
                if "Scan axis,Omega" in clean_line or "Scan axis, Omega" in clean_line:
                    metadata["scan_axis"] = "Omega"
                
                # Check for fixed angles during the scan
                elif clean_line.startswith("2Theta,"):
                    parts = clean_line.split(",")
                    if len(parts) >= 2:
                        metadata["fixed_2theta"] = float(parts[1].strip())
                elif clean_line.startswith("Omega,"):
                    parts = clean_line.split(",")
                    if len(parts) >= 2:
                        metadata["fixed_omega"] = float(parts[1].strip())
                
                # Stop parsing metadata once we hit the data block
                if "[Scan points]" in clean_line or "[Data]" in clean_line:
                    break
        except Exception as e:
            logger.warning("Failed to extract metadata: %s", e)

        return metadata

    def load(self, filepath: str | Path) -> pd.DataFrame:
        """
        Read an XRD CSV file and return a clean DataFrame.
        """
        filepath = Path(filepath)
        logger.info("Loading CSV from path: %s", filepath)

        df = self._read_raw(filepath)
        df = self._normalise_columns(df)
        df = self._clean(df)
        self._validate(df)

        logger.info(
            "CSV loaded successfully — %d rows, X-Axis range %.6f°–%.6f°",
            len(df),
            df["two_theta"].min(),
            df["two_theta"].max(),
        )
        return df

    def load_bytes(self, content: bytes, filename: str = "upload.csv") -> pd.DataFrame:
        """
        Parse CSV from raw bytes (e.g. from an HTTP upload).
        """
        logger.info("Parsing CSV bytes for file: %s", filename)

        # Detect and skip instrument metadata header lines dynamically
        skiprows = self._detect_header_rows_from_bytes(content)
        parsed_raw = None

        # Step 1: Scan using multiple potential separators matching the calculated skiprows offset
        for sep in (",", ";", "\t", " "):
            try:
                raw = pd.read_csv(
                    io.BytesIO(content),
                    sep=sep,
                    engine="python",
                    skip_blank_lines=True,
                    skiprows=skiprows,
                )
                if raw.shape[1] >= 2 and self._has_valid_columns(raw):
                    parsed_raw = raw
                    break
            except Exception:
                continue

        # Step 2: Fallback to Row 0 index if the custom metadata offset skipped critical definitions
        if parsed_raw is None and skiprows > 0:
            for sep in (",", ";", "\t", " "):
                try:
                    raw = pd.read_csv(
                        io.BytesIO(content),
                        sep=sep,
                        engine="python",
                        skip_blank_lines=True,
                        skiprows=0,
                    )
                    if raw.shape[1] >= 2 and self._has_valid_columns(raw):
                        parsed_raw = raw
                        break
                except Exception:
                    continue

        # Step 3: Absolute structural fallback to catch remaining edge-cases
        if parsed_raw is None:
            for sep in (",", ";", "\t", " "):
                try:
                    parsed_raw = pd.read_csv(io.BytesIO(content), sep=sep, engine="python", skiprows=skiprows)
                    break
                except Exception:
                    continue

        if parsed_raw is None:
            raise CSVReadError(f"Failed to decode or parse raw file bytes structural layout for '{filename}'.")

        df = self._normalise_columns(parsed_raw)
        df = self._clean(df)
        self._validate(df)
        return df

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect_skiprows(self, lines: list[str]) -> int:
        """Scans string line rows sequentially to extract metadata offsets."""
        # Check explicit bracketed markers
        for i, line in enumerate(lines):
            clean = line.strip().lower()
            if clean == "[scan points]" or clean == "[data]":
                return i + 1

        # Check token alignments directly
        for i, line in enumerate(lines):
            for sep in (",", ";", "\t"):
                parts = [p.strip().lower() for p in line.split(sep)]
                if len(parts) >= 2:
                    has_theta = any(p in TWO_THETA_ALIASES or p.replace(" ", "_") in TWO_THETA_ALIASES for p in parts)
                    has_intensity = any(p in INTENSITY_ALIASES or p.replace(" ", "_") in INTENSITY_ALIASES for p in parts)
                    if has_theta and has_intensity:
                        return i
        return 0

    def _detect_header_rows(self, filepath: Path) -> int:
        """Scan the file for an instrument configuration metadata offset size."""
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = [f.readline() for _ in range(300)]
            return self._detect_skiprows(lines)
        except Exception:
            pass
        return 0

    def _detect_header_rows_from_bytes(self, content: bytes) -> int:
        """Same as _detect_header_rows but operates on raw bytes inputs."""
        try:
            text = content.decode("utf-8", errors="replace")
            return self._detect_skiprows(text.splitlines()[:300])
        except Exception:
            pass
        return 0

    def _has_valid_columns(self, df: pd.DataFrame) -> bool:
        """Validates if the structural columns can map to application properties safely."""
        has_theta = False
        has_intensity = False
        for col in df.columns:
            normalised = (
                str(col).strip()
                .lower()
                .replace(" ", "_")
                .replace("(", "")
                .replace(")", "")
                .replace("°", "")
            )
            col_lower = str(col).strip().lower()
            if normalised in TWO_THETA_ALIASES or col_lower in TWO_THETA_ALIASES:
                has_theta = True
            elif normalised in INTENSITY_ALIASES or col_lower in INTENSITY_ALIASES:
                has_intensity = True
        return has_theta and has_intensity

    def _read_raw(self, filepath: Path) -> pd.DataFrame:
        """Attempt to read the CSV, trying common delimiters and header structures."""
        if not filepath.exists():
            raise CSVReadError(f"File not found on system: {filepath}")

        skiprows = self._detect_header_rows(filepath)

        # Primary pass matching dynamic offset headers
        for sep in (",", ";", "\t", " "):
            try:
                df = pd.read_csv(
                    filepath,
                    sep=sep,
                    engine="python",
                    skip_blank_lines=True,
                    skiprows=skiprows,
                )
                if df.shape[1] >= 2 and self._has_valid_columns(df):
                    return df
            except Exception:
                continue

        # Secondary fallback from root position
        if skiprows > 0:
            for sep in (",", ";", "\t", " "):
                try:
                    df = pd.read_csv(
                        filepath,
                        sep=sep,
                        engine="python",
                        skip_blank_lines=True,
                        skiprows=0,
                    )
                    if df.shape[1] >= 2 and self._has_valid_columns(df):
                        return df
                except Exception:
                    continue

        # Absolute default read operation to feed downstream normalization diagnostics
        for sep in (",", ";", "\t", " "):
            try:
                return pd.read_csv(filepath, sep=sep, engine="python", skiprows=skiprows)
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
            normalised = (
                str(col).strip()
                .lower()
                .replace(" ", "_")
                .replace("(", "")
                .replace(")", "")
                .replace("°", "")
            )
            col_lower = str(col).strip().lower()
            if normalised in TWO_THETA_ALIASES or col_lower in TWO_THETA_ALIASES:
                mapping[col] = "two_theta" # Maps Omega or Angle to "two_theta" for internal consistency
            elif normalised in INTENSITY_ALIASES or col_lower in INTENSITY_ALIASES:
                mapping[col] = "intensity"

        if "two_theta" not in mapping.values():
            raise CSVReadError(
                f"No Angle/2θ column found. Expected one of: {sorted(TWO_THETA_ALIASES)}. "
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
        """Coerce types, drop NaN/negative rows, sort by Angle."""
        df = df.copy()
        df["two_theta"] = pd.to_numeric(df["two_theta"], errors="coerce")
        df["intensity"] = pd.to_numeric(df["intensity"], errors="coerce")
        df = df.dropna(subset=["two_theta", "intensity"])
        df = df[df["intensity"] >= 0]            # Drop unphysical negative counts
        
        # UPGRADE: Expanded physical range from (0, 180) to (-360, 360) 
        # Omega Scans can frequently go negative or hover near 0.
        df = df[df["two_theta"].between(-360, 360)] 
        
        df = df.sort_values("two_theta").reset_index(drop=True)
        
        # np.float64 inherently preserves 15+ digits of decimal precision
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


# ----------------------------------------------------------------------
# Quick smoke-test — run directly to verify a file
# Usage: python services/csv_reader.py path/to/file.csv
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else None
    if not path:
        print("Usage: python csv_reader.py <path_to_csv>")
        sys.exit(1)

    reader = CSVReader()
    
    # Test Metadata extraction
    meta = reader.extract_metadata(path)
    print(f"Scan Metadata: {meta}")
    
    # Test load
    result = reader.load(path)
    print(result.head(10).to_string(index=False))
    print(f"\nTotal points : {len(result)}")
    print(f"Angle range  : {result['two_theta'].min():.6f}° – {result['two_theta'].max():.6f}°")
    print(f"Max intensity: {result['intensity'].max():.1f}")