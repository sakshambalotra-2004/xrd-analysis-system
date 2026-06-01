import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ReportDownload from "../components/ReportDownload";

/**
 * Reports Page
 * ============
 * Lists all analyses that have a completed PDF report available,
 * with per-row download buttons.
 */
export default function ReportsPage() {
  const navigate = useNavigate();
  const [reports, setReports] = useState([]);

  useEffect(() => {
    const stored = JSON.parse(localStorage.getItem("xrd_recent") || "[]");
    setReports(stored);
  }, []);

  return (
    <div className="page reports-page">
      <div className="page-header">
        <h1>Reports</h1>
        <p className="subtitle">Download PDF reports for completed analyses.</p>
      </div>

      {reports.length === 0 ? (
        <div className="empty-state">
          <p>No completed analyses found.</p>
          <button className="btn btn-primary" onClick={() => navigate("/upload")}>
            Start a new analysis
          </button>
        </div>
      ) : (
        <div className="reports-list">
          {reports.map((r) => (
            <ReportDownload key={r.file_id} result={r} />
          ))}
        </div>
      )}
    </div>
  );
}