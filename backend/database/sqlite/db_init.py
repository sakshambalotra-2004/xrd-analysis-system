"""
database/sqlite/db_init.py
==========================
SQLite connection and schema initialisation for the XRD analysis system.

Schema is kept in sync with utils/file_handler.py column expectations.
"""

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# Database file sits in the same directory as this file
DB_PATH = Path(__file__).parent / "xrd_database.db"


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row_factory for dict-like row access."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    # Enable foreign key enforcement
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create all tables if they do not already exist."""
    conn = get_connection()
    try:
        conn.executescript("""
            -- ----------------------------------------------------------------
            -- experiments
            -- One row per uploaded CSV file.
            -- ----------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS experiments (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id     TEXT    NOT NULL UNIQUE,   -- UUID assigned at upload
                filename    TEXT    NOT NULL,
                file_path   TEXT    NOT NULL,
                rows        INTEGER DEFAULT 0,
                status      TEXT    DEFAULT 'uploaded',
                uploaded_at TEXT    DEFAULT (datetime('now'))
            );

            -- ----------------------------------------------------------------
            -- analysis_results
            -- One row per completed analysis (keyed by file_id).
            -- ----------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS analysis_results (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id               TEXT    NOT NULL UNIQUE REFERENCES experiments(file_id),
                compound_name         TEXT,
                formula               TEXT,
                crystal_system        TEXT,
                space_group           TEXT,
                confidence_score      REAL,
                crystallite_size_nm   REAL,
                mean_peak_shift_deg   REAL,
                strain_indicator      TEXT,
                detected_phases       TEXT,   -- JSON array
                graph_experimental    TEXT,
                graph_standard        TEXT,
                graph_overlay         TEXT,
                report_pdf            TEXT,
                analysed_at           TEXT    DEFAULT (datetime('now'))
            );

            -- ----------------------------------------------------------------
            -- peaks
            -- One row per detected peak per experiment.
            -- ----------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS peaks (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id       TEXT    NOT NULL REFERENCES experiments(file_id),
                two_theta     REAL,
                intensity     REAL,
                fwhm_deg      REAL,
                prominence    REAL
            );

            -- ----------------------------------------------------------------
            -- compounds  (cached standard compound index)
            -- ----------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS compounds (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                compound_name  TEXT,
                formula        TEXT,
                crystal_system TEXT,
                space_group    TEXT,
                json_path      TEXT
            );
        """)
        conn.commit()
        logger.info("Database initialised at %s", DB_PATH)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Auto-initialise on import so every module that calls get_connection()
# is guaranteed to find the schema in place.
# ---------------------------------------------------------------------------
init_db()