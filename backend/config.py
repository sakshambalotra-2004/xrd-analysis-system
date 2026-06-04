"""
backend/config.py
=================
Centralised configuration via Pydantic BaseSettings.
"""

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_TITLE: str = "XRD Compound Identification and Analysis System"
    APP_DESCRIPTION: str = "Automated X-Ray Diffraction analysis."
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    UPLOAD_MAX_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".txt"]

    # Directory layout (relative to backend/)
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

    UPLOAD_BASE_DIR: str = os.path.join(BASE_DIR, "uploads")
    UPLOAD_CSV_DIR: str = os.path.join(BASE_DIR, "uploads", "csv")
    UPLOAD_TEMP_DIR: str = os.path.join(BASE_DIR, "uploads", "temp")

    DB_BASE_DIR: str = os.path.join(BASE_DIR, "database")
    STANDARDS_DIR: str = os.path.join(BASE_DIR, "database", "standards")
    EXPERIMENTAL_DATA_DIR: str = os.path.join(BASE_DIR, "database", "experimental_data")
    SQLITE_DIR: str = os.path.join(BASE_DIR, "database", "sqlite")
    SQLITE_DB_PATH: str = os.path.join(BASE_DIR, "database", "sqlite", "xrd_database.db")

    # Reports / output folders
    REPORTS_BASE_DIR: str = os.path.join(BASE_DIR, "reports")
    REPORTS_PDF_DIR: str = os.path.join(BASE_DIR, "reports", "pdf_reports")
    REPORTS_GRAPHS_DIR: str = os.path.join(BASE_DIR, "reports", "graphs")
    REPORTS_OVERLAY_DIR: str = os.path.join(BASE_DIR, "reports", "overlay_images")
    
    # NEWLY FIXED: Anchoring the automated Origin paths explicitly in config settings
    REPORTS_ORIGIN_FILES_DIR: str = os.path.join(BASE_DIR, "reports", "origin_files")
    REPORTS_ORIGIN_IMAGES_DIR: str = os.path.join(BASE_DIR, "reports", "origin_images")

    MODELS_DIR: str = os.path.join(BASE_DIR, "models")
    MODEL_PATH: str = os.path.join(BASE_DIR, "models", "trained_model.pkl")
    SCALER_PATH: str = os.path.join(BASE_DIR, "models", "scaler.pkl")
    LABEL_ENCODER_PATH: str = os.path.join(BASE_DIR, "models", "label_encoder.pkl")

    WAVELENGTH_ANGSTROM: float = 1.5406
    BRAGG_ORDER: int = 1
    SCHERRER_K: float = 0.9

    PEAK_HEIGHT_THRESHOLD: float = 0.05
    PEAK_MIN_DISTANCE: int = 25
    PEAK_PROMINENCE: float = 0.05

    NOISE_FILTER_WINDOW: int = 35
    NOISE_FILTER_POLYORDER: int = 3

    PEAK_MATCH_TOLERANCE_DEG: float = 0.2
    MIN_SIMILARITY_SCORE: float = 40.0
    MAX_CANDIDATES: int = 5

    REPORT_DPI: int = 150
    REPORT_GRAPH_FORMAT: str = "png"

    MONGODB_ENABLED: bool = False
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "xrd_analysis"

    @property
    def upload_max_bytes(self) -> int:
        return self.UPLOAD_MAX_SIZE_MB * 1024 * 1024

    @property
    def wavelength_nm(self) -> float:
        return self.WAVELENGTH_ANGSTROM / 10.0

settings = Settings()