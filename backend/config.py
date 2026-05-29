"""
XRD Compound Identification and Analysis System
================================================
Centralised configuration via Pydantic BaseSettings.

All values can be overridden through environment variables or a `.env` file
placed at the project root.

Usage:
    from config import settings
    print(settings.UPLOAD_MAX_SIZE_MB)
"""

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application-wide settings.

    Environment variables are matched case-insensitively and read from a
    `.env` file when present.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -----------------------------------------------------------------------
    # Application metadata
    # -----------------------------------------------------------------------
    APP_TITLE: str = "XRD Compound Identification and Analysis System"
    APP_DESCRIPTION: str = (
        "Automated X-Ray Diffraction analysis: peak detection, compound "
        "identification, crystallographic analysis, and PDF report generation."
    )
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # -----------------------------------------------------------------------
    # Server
    # -----------------------------------------------------------------------
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # -----------------------------------------------------------------------
    # CORS
    # -----------------------------------------------------------------------
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # Optional CRA / other dev server
        "http://127.0.0.1:5173",
    ]

    # -----------------------------------------------------------------------
    # File upload
    # -----------------------------------------------------------------------
    UPLOAD_MAX_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".txt"]

    # -----------------------------------------------------------------------
    # Directory layout (relative to backend/)
    # -----------------------------------------------------------------------
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

    # Uploads
    UPLOAD_BASE_DIR: str = os.path.join(BASE_DIR, "uploads")
    UPLOAD_CSV_DIR: str = os.path.join(BASE_DIR, "uploads", "csv")
    UPLOAD_TEMP_DIR: str = os.path.join(BASE_DIR, "uploads", "temp")

    # Database
    DB_BASE_DIR: str = os.path.join(BASE_DIR, "database")
    STANDARDS_DIR: str = os.path.join(BASE_DIR, "database", "standards")
    EXPERIMENTAL_DATA_DIR: str = os.path.join(BASE_DIR, "database", "experimental_data")
    SQLITE_DIR: str = os.path.join(BASE_DIR, "database", "sqlite")
    SQLITE_DB_PATH: str = os.path.join(BASE_DIR, "database", "sqlite", "xrd_database.db")

    # Reports / output
    REPORTS_BASE_DIR: str = os.path.join(BASE_DIR, "reports")
    REPORTS_PDF_DIR: str = os.path.join(BASE_DIR, "reports", "pdf_reports")
    REPORTS_GRAPHS_DIR: str = os.path.join(BASE_DIR, "reports", "graphs")
    REPORTS_OVERLAY_DIR: str = os.path.join(BASE_DIR, "reports", "overlay_images")

    # ML models
    MODELS_DIR: str = os.path.join(BASE_DIR, "models")
    MODEL_PATH: str = os.path.join(BASE_DIR, "models", "trained_model.pkl")
    SCALER_PATH: str = os.path.join(BASE_DIR, "models", "scaler.pkl")
    LABEL_ENCODER_PATH: str = os.path.join(BASE_DIR, "models", "label_encoder.pkl")

    # -----------------------------------------------------------------------
    # XRD physical / experimental constants
    # -----------------------------------------------------------------------
    # Cu Kα radiation wavelength in Ångströms (default X-ray source)
    WAVELENGTH_ANGSTROM: float = 1.5406

    # Bragg's Law: nλ = 2d sin θ  (n = 1 for first-order diffraction)
    BRAGG_ORDER: int = 1

    # Scherrer constant K (dimensionless shape factor, typically 0.89–1.0)
    SCHERRER_K: float = 0.9

    # -----------------------------------------------------------------------
    # Peak detection
    # -----------------------------------------------------------------------
    # Minimum peak height as a fraction of the global maximum intensity
    PEAK_HEIGHT_THRESHOLD: float = 0.05     # 5 % of max intensity

    # Minimum distance between two adjacent peaks (in 2θ data points)
    PEAK_MIN_DISTANCE: int = 10

    # Prominence threshold for scipy.signal.find_peaks
    PEAK_PROMINENCE: float = 0.02

    # -----------------------------------------------------------------------
    # Noise filtering
    # -----------------------------------------------------------------------
    # Savitzky-Golay filter window length (must be odd)
    NOISE_FILTER_WINDOW: int = 11

    # Savitzky-Golay polynomial order
    NOISE_FILTER_POLYORDER: int = 3

    # -----------------------------------------------------------------------
    # Peak matching
    # -----------------------------------------------------------------------
    # Maximum allowed difference |2θ_exp − 2θ_std| for a match (degrees)
    PEAK_MATCH_TOLERANCE_DEG: float = 0.2

    # Minimum similarity score (%) to consider a compound a valid match
    MIN_SIMILARITY_SCORE: float = 40.0

    # Maximum number of candidate compounds returned in results
    MAX_CANDIDATES: int = 5

    # -----------------------------------------------------------------------
    # Report generation
    # -----------------------------------------------------------------------
    REPORT_DPI: int = 150            # DPI for embedded graph images
    REPORT_GRAPH_FORMAT: str = "png"

    # -----------------------------------------------------------------------
    # Optional: MongoDB (disabled by default)
    # -----------------------------------------------------------------------
    MONGODB_ENABLED: bool = False
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "xrd_analysis"

    # -----------------------------------------------------------------------
    # Derived helpers (not environment variables)
    # -----------------------------------------------------------------------
    @property
    def upload_max_bytes(self) -> int:
        """Maximum upload size in bytes."""
        return self.UPLOAD_MAX_SIZE_MB * 1024 * 1024

    @property
    def wavelength_nm(self) -> float:
        """Cu Kα wavelength in nanometres."""
        return self.WAVELENGTH_ANGSTROM / 10.0


# ---------------------------------------------------------------------------
# Singleton instance — import this everywhere
# ---------------------------------------------------------------------------
settings = Settings()