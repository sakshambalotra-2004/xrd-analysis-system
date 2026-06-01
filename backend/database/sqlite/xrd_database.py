"""
database/sqlite/db_init.py
==========================
SQLite database initialisation for the XRD Analysis System.

Creates all required tables on first run (idempotent — safe to call on
every startup via the FastAPI lifespan hook).

Schema
------
experiments
    Metadata for every uploaded CSV file.

analysis_results
    One row per completed analysis run; stores crystallographic outputs
    and file paths for graphs and PDF reports.

peaks
    Detected peaks for each experiment (one row per peak).

compounds
    Cached index of standard compound names loaded from JSON files.
"""

import logging
import sqlite3
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)

CREATE_EXPERIMENTS = """
CREATE TABLE IF NOT EXISTS experiments (
    file_id       TEXT PRIMARY KEY,
    filename      TEXT NOT NULL,
    file_path     TEXT NOT NULL,
    rows          INTEGER NOT NULL,
    status        TEXT NOT NULL DEFAULT 'uploaded',
    uploaded_at   TEXT NOT NULL
);
"""

CREATE_ANALYSIS_RESULTS = """
CREATE TABLE IF NOT EXISTS analysis_results (
    file_id               TEXT PRIMARY KEY,
    compound_name         TEXT,
    formula               TEXT,
    crystal_system        TEXT,
    space_group           TEXT,
    confidence_score      REAL,
    crystallite_size_nm   REAL,
    mean_peak_shift_deg   REAL,
    strain_indicator      TEXT,
    detected_phases       TEXT,    -- JSON-encoded list
    graph_experimental    TEXT,
    graph_standard        TEXT,
    graph_overlay         TEXT,
    report_pdf            TEXT,
    analysed_at           TEXT,
    FOREIGN KEY (file_id) REFERENCES experiments(file_id) ON DELETE CASCADE
);
"""

CREATE_PEAKS = """
CREATE TABLE IF NOT EXISTS peaks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id     TEXT NOT NULL,
    two_theta   REAL NOT NULL,
    intensity   REAL NOT NULL,
    fwhm_deg    REAL,
    prominence  REAL,
    FOREIGN KEY (file_id) REFERENCES experiments(file_id) ON DELETE CASCADE
);
"""

CREATE_COMPOUNDS = """
CREATE TABLE IF NOT EXISTS compounds (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    compound_name   TEXT NOT NULL UNIQUE,
    formula         TEXT,
    crystal_system  TEXT,
    space_group     TEXT,
    json_filename   TEXT
);
"""

# Indexes for common query patterns
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_peaks_file_id ON peaks (file_id);",
    "CREATE INDEX IF NOT EXISTS idx_results_compound ON analysis_results (compound_name);",
]


def init_db(db_path: str | None = None) -> None:
    """
    Create all tables and indexes if they do not already exist.

    Parameters
    ----------
    db_path : str | None
        Path to the SQLite database file.  Defaults to ``settings.SQLITE_DB_PATH``.
    """
    path = db_path or settings.SQLITE_DB_PATH
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL;")   # safer concurrent access
    con.execute("PRAGMA foreign_keys=ON;")

    for ddl in [CREATE_EXPERIMENTS, CREATE_ANALYSIS_RESULTS, CREATE_PEAKS, CREATE_COMPOUNDS]:
        con.execute(ddl)

    for idx_sql in CREATE_INDEXES:
        con.execute(idx_sql)

    con.commit()
    con.close()
    logger.info("SQLite database initialised at: %s", path)


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """
    Return a configured SQLite connection with row_factory set to
    ``sqlite3.Row`` for dict-like row access.

    The caller is responsible for closing the connection.
    """
    path = db_path or settings.SQLITE_DB_PATH
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON;")
    return con