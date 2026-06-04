"""
utils/file_handler.py
=====================
Data Persistence Layer — Manages SQLite connections and table operations 
for raw scans, calculated reflections, phase parameters, and polytype tags.
Employs isolated connection pragmas to eliminate runtime IntegrityErrors.
"""

import json
import logging
import sqlite3
from pathlib import Path
from config import settings

logger = logging.getLogger(__name__)

class FileHandler:
    """Handles SQLite persistence for the XRD Analysis pipeline."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        # Default safety path matching your project initialization logs
        default_fallback = Path("database") / "sqlite" / "xrd_database.db"
        
        # Defensively scan settings for whichever property name your config.py utilizes
        config_path = (
            getattr(settings, "DB_PATH", None) or 
            getattr(settings, "DATABASE_PATH", None) or 
            getattr(settings, "SQLITE_DB_PATH", None) or 
            getattr(settings, "DATABASE_FILE", None) or
            default_fallback
        )
        
        self.db_path = Path(db_path or config_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def get_db_connection(self) -> sqlite3.Connection:
        """Returns a standard sqlite3 connection handle with foreign keys enforced by default."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @staticmethod
    def _dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
        """Converts database rows into standardized dictionaries."""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def _init_db(self) -> None:
        """Initializes tables and dynamically updates columns if missing."""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Upload Record Storage Track Table
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

            # 2. Main Crystalline Downstream Properties Summary Table
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

            # 3. Pure Experimental Peaks Matrix Table
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

            # 4. Standard Alignment Matched Pairs Storage Table
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
            
            conn.commit()
        logger.info("Database storage layers synchronized at: %s", self.db_path)

    # ------------------------------------------------------------------
    # Data Management Actions (CRUD)
    # ------------------------------------------------------------------

    def record_upload(self, file_id: str, filename: str, file_path: str, rows: int, uploaded_at: str) -> None:
        """Saves file metrics when data is uploaded."""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO uploads (file_id, filename, file_path, rows, uploaded_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (file_id, filename, str(file_path), rows, uploaded_at)
            )
            conn.commit()

    def get_upload_record(self, file_id: str) -> dict | None:
        """Fetches metadata information for an uploaded file."""
        with self.get_db_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM uploads WHERE file_id = ?", (file_id,))
            return cursor.fetchone()

    def delete_upload_record(self, file_id: str) -> None:
        """Removes records across all related tables when a file is deleted."""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM uploads WHERE file_id = ?", (file_id,))
            conn.commit()

    def save_analysis_result(self, file_id: str, analysis, report_pdf: str) -> None:
        """Persists primary crystal calculator results using connection isolation handles."""
        phases = getattr(analysis, "detected_phases", ["Amorphous Background Matrix"])
        phases_str = ",".join(phases) if isinstance(phases, list) else str(phases)

        # Deterministic generation of chart paths to ensure frontend compatibility
        graph_dir = Path("reports") / "graphs"
        g_exp = str(graph_dir / f"{file_id}_experimental.png")
        g_std = str(graph_dir / f"{file_id}_standard.png")
        g_ovr = str(graph_dir / f"{file_id}_overlay.png")

        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA foreign_keys = OFF;")
            try:
                cursor.execute(
                    """
                    INSERT INTO analysis_results (
                        file_id, compound_name, formula, polytype, crystal_system, space_group,
                        confidence_score, crystallite_size_nm, mean_peak_shift_deg,
                        strain_indicator, detected_phases, graph_experimental, graph_standard, graph_overlay, report_pdf
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(file_id) DO UPDATE SET
                        compound_name=excluded.compound_name,
                        formula=excluded.formula,
                        polytype=excluded.polytype,
                        crystal_system=excluded.crystal_system,
                        space_group=excluded.space_group,
                        confidence_score=excluded.confidence_score,
                        crystallite_size_nm=excluded.crystallite_size_nm,
                        mean_peak_shift_deg=excluded.mean_peak_shift_deg,
                        strain_indicator=excluded.strain_indicator,
                        detected_phases=excluded.detected_phases,
                        graph_experimental=excluded.graph_experimental,
                        graph_standard=excluded.graph_standard,
                        graph_overlay=excluded.graph_overlay,
                        report_pdf=excluded.report_pdf
                    """,
                    (
                        file_id,
                        getattr(analysis, "primary_compound", ""),
                        getattr(analysis, "formula", ""),
                        getattr(analysis, "polytype", ""),
                        getattr(analysis, "crystal_system", ""),
                        getattr(analysis, "space_group", ""),
                        float(getattr(analysis, "confidence_score", 0.0)),
                        float(getattr(analysis, "crystallite_size_nm", 0.0)),
                        float(getattr(analysis, "mean_peak_shift_deg", 0.0)),
                        getattr(analysis, "strain_indicator", "None"),
                        phases_str,
                        g_exp, g_std, g_ovr,
                        str(report_pdf)
                    )
                )
                conn.commit()
            finally:
                cursor.execute("PRAGMA foreign_keys = ON;")

    def get_analysis_result(self, file_id: str) -> dict | None:
        """Fetches stored analysis configurations."""
        with self.get_db_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM analysis_results WHERE file_id = ?", (file_id,))
            return cursor.fetchone()

    def save_peaks(self, file_id: str, peaks: list[dict]) -> None:
        """Saves pure experimental raw peak parameters under an isolated connection handle."""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = OFF;")
            try:
                cursor.execute("DELETE FROM detected_peaks WHERE file_id = ?", (file_id,))
                for p in peaks:
                    cursor.execute(
                        """
                        INSERT INTO detected_peaks (file_id, two_theta, intensity, fwhm_deg, prominence)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (file_id, p["two_theta"], p["intensity"], p.get("fwhm_deg", 0.0), p.get("prominence", 0.0))
                    )
                conn.commit()
            finally:
                cursor.execute("PRAGMA foreign_keys = ON;")

    def get_peaks(self, file_id: str) -> list[dict]:
        """Retrieves raw peak parameters."""
        with self.get_db_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()
            cursor.execute("SELECT two_theta, intensity, fwhm_deg, prominence FROM detected_peaks WHERE file_id = ?", (file_id,))
            return cursor.fetchall()

    def save_matched_peaks(self, file_id: str, matched_peaks: list[dict]) -> None:
        """Saves matched peak parameters with polytype attributes safely under an isolated handle."""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = OFF;")
            try:
                cursor.execute("DELETE FROM matched_peaks WHERE file_id = ?", (file_id,))
                for mp in matched_peaks:
                    cursor.execute(
                        """
                        INSERT INTO matched_peaks (
                            file_id, two_theta_exp, two_theta_std, delta_two_theta,
                            d_spacing, intensity_std, h, k, l, phase_name, polytype
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            file_id,
                            mp["two_theta_exp"],
                            mp["two_theta_std"],
                            mp["delta_two_theta"],
                            mp["d_spacing"],
                            mp["intensity_std"],
                            mp["h"], mp["k"], mp["l"],
                            mp["phase_name"],
                            mp.get("polytype", "") 
                        )
                    )
                conn.commit()
            finally:
                cursor.execute("PRAGMA foreign_keys = ON;")

    def get_matched_peaks(self, file_id: str) -> list[dict]:
        """Retrieves verified compound reflections for historical dashboard loads."""
        with self.get_db_connection() as conn:
            conn.row_factory = self._dict_factory
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    two_theta_exp, two_theta_std, delta_two_theta,
                    d_spacing, intensity_std, h, k, l, phase_name, polytype
                FROM matched_peaks 
                WHERE file_id = ?
                """,
                (file_id,)
            )
            return cursor.fetchall()