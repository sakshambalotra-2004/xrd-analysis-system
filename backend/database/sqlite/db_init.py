"""
database/sqlite/db_init.py
==========================
SQLite connection and schema initialisation for the XRD analysis system.

Schema is fully synchronized with utils/file_handler.py and analysis_routes.py 
to eliminate foreign key constraint violations and property alignment crashes.
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
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Create all tables if they do not already exist with updated schema rules."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 1. uploads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uploads (
                file_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                rows INTEGER NOT NULL,
                status TEXT DEFAULT 'uploaded',
                uploaded_at TEXT NOT NULL
            );
        """)

        # 2. analysis_results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                file_id TEXT PRIMARY KEY,
                compound_name TEXT,
                formula TEXT,
                polytype TEXT,
                crystal_system TEXT,
                space_group TEXT,
                confidence_score REAL,
                crystallite_size_nm REAL,
                mean_peak_shift_deg REAL,
                strain_indicator TEXT,
                detected_phases TEXT,
                graph_experimental TEXT,
                graph_standard TEXT,
                graph_overlay TEXT,
                report_pdf TEXT,
                analysed_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(file_id) REFERENCES uploads(file_id) ON DELETE CASCADE
            );
        """)

        # 3. detected_peaks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detected_peaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT NOT NULL,
                two_theta REAL NOT NULL,
                intensity REAL NOT NULL,
                fwhm_deg REAL,
                prominence REAL,
                FOREIGN KEY(file_id) REFERENCES uploads(file_id) ON DELETE CASCADE
            );
        """)

        # 4. matched_peaks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matched_peaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT NOT NULL,
                two_theta_exp REAL NOT NULL,
                two_theta_std REAL NOT NULL,
                delta_two_theta REAL NOT NULL,
                d_spacing REAL NOT NULL,
                intensity_std REAL NOT NULL,
                h INTEGER,
                k INTEGER,
                l INTEGER,
                phase_name TEXT,
                polytype TEXT,
                FOREIGN KEY(file_id) REFERENCES uploads(file_id) ON DELETE CASCADE
            );
        """)

        # 5. compounds table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compound_name TEXT,
                formula TEXT,
                crystal_system TEXT,
                space_group TEXT,
                json_path TEXT
            );
        """)

        conn.commit()
        logger.info("Database unified schema successfully initialized at %s", DB_PATH)
    except Exception as e:
        logger.error("Failed to initialize database schema: %s", e)
        raise e
    finally:
        conn.close()


# Auto-initialise on import
init_db()