"""
utils/file_handler.py
=====================
File Handler — persistence layer wrapper around the SQLite database.

Provides a simple interface for storing and retrieving upload metadata
and analysis results, keeping raw SQL out of routes and services.
"""

import json
import logging
from datetime import datetime
from typing import Any

from database.sqlite.db_init import get_connection
from services.crystal_analyzer import CrystalAnalysis

logger = logging.getLogger(__name__)


class FileHandler:
    """CRUD operations for experiments and analysis_results tables."""

    # ------------------------------------------------------------------
    # Upload records
    # ------------------------------------------------------------------

    def record_upload(
        self,
        file_id: str,
        filename: str,
        file_path: str,
        rows: int,
        uploaded_at: str | None = None,
    ) -> None:
        """Insert a new experiment record into the experiments table."""
        uploaded_at = uploaded_at or datetime.utcnow().isoformat()
        con = get_connection()
        try:
            con.execute(
                """
                INSERT INTO experiments (file_id, filename, file_path, rows, status, uploaded_at)
                VALUES (?, ?, ?, ?, 'uploaded', ?)
                """,
                (file_id, filename, file_path, rows, uploaded_at),
            )
            con.commit()
        finally:
            con.close()

    def get_upload_record(self, file_id: str) -> dict | None:
        """Retrieve upload metadata for a file_id. Returns None if not found."""
        con = get_connection()
        try:
            row = con.execute(
                "SELECT * FROM experiments WHERE file_id = ?", (file_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            con.close()

    def delete_upload_record(self, file_id: str) -> None:
        """Delete an experiment record (cascades to peaks and analysis_results)."""
        con = get_connection()
        try:
            con.execute("DELETE FROM experiments WHERE file_id = ?", (file_id,))
            con.commit()
        finally:
            con.close()

    def update_status(self, file_id: str, status: str) -> None:
        """Update the processing status of an experiment."""
        con = get_connection()
        try:
            con.execute(
                "UPDATE experiments SET status = ? WHERE file_id = ?",
                (status, file_id),
            )
            con.commit()
        finally:
            con.close()

    # ------------------------------------------------------------------
    # Analysis results
    # ------------------------------------------------------------------

    def save_analysis_result(
        self,
        file_id: str,
        analysis: CrystalAnalysis,
        pdf_path: str,
        graph_experimental: str = "",
        graph_standard: str = "",
        graph_overlay: str = "",
    ) -> None:
        """Persist a CrystalAnalysis result into the analysis_results table."""
        con = get_connection()
        try:
            con.execute(
                """
                INSERT OR REPLACE INTO analysis_results (
                    file_id, compound_name, formula, crystal_system, space_group,
                    confidence_score, crystallite_size_nm, mean_peak_shift_deg,
                    strain_indicator, detected_phases,
                    graph_experimental, graph_standard, graph_overlay,
                    report_pdf, analysed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    file_id,
                    analysis.primary_compound,
                    analysis.formula,
                    analysis.crystal_system,
                    analysis.space_group,
                    analysis.confidence_score,
                    analysis.crystallite_size_nm,
                    analysis.mean_peak_shift_deg,
                    analysis.strain_indicator,
                    json.dumps(analysis.detected_phases),
                    graph_experimental,
                    graph_standard,
                    graph_overlay,
                    pdf_path,
                    datetime.utcnow().isoformat(),
                ),
            )
            con.commit()
            self.update_status(file_id, "done")
        finally:
            con.close()

    def get_analysis_result(self, file_id: str) -> dict[str, Any] | None:
        """Retrieve a stored analysis result dict. Returns None if not found."""
        con = get_connection()
        try:
            row = con.execute(
                "SELECT * FROM analysis_results WHERE file_id = ?", (file_id,)
            ).fetchone()
            if not row:
                return None
            d = dict(row)
            d["detected_phases"] = json.loads(d.get("detected_phases") or "[]")
            return d
        finally:
            con.close()

    # ------------------------------------------------------------------
    # Peaks
    # ------------------------------------------------------------------

    def save_peaks(self, file_id: str, peaks: list[dict]) -> None:
        """Bulk-insert detected peaks for a file_id."""
        con = get_connection()
        try:
            con.executemany(
                """
                INSERT INTO peaks (file_id, two_theta, intensity, fwhm_deg, prominence)
                VALUES (:file_id, :two_theta, :intensity, :fwhm_deg, :prominence)
                """,
                [{"file_id": file_id, **p} for p in peaks],
            )
            con.commit()
        finally:
            con.close()

    def get_peaks(self, file_id: str) -> list[dict]:
        """Retrieve all peaks for a file_id."""
        con = get_connection()
        try:
            rows = con.execute(
                "SELECT * FROM peaks WHERE file_id = ? ORDER BY two_theta", (file_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            con.close()