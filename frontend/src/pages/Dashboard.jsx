import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { analysisApi } from "../api/analysisApi";
import ConfidenceCard from "../components/ConfidenceCard";
import AnalysisSummary from "../components/AnalysisSummary";

/**
 * Dashboard Page
 * ==============
 * Landing page showing:
 *  - Quick stats (total analyses, avg confidence, most common compound)
 *  - Recent analysis cards
 *  - Quick-upload CTA
 */
export default function Dashboard() {
  const navigate = useNavigate();
  const [recentResults, setRecentResults] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load recent analyses from localStorage (persisted on ResultsPage)
    const stored = JSON.parse(localStorage.getItem("xrd_recent") || "[]");
    setRecentResults(stored.slice(0, 5));
    setLoading(false);
  }, []);

  const handleQuickUpload = () => navigate("/upload");

  return (
    <div className="page dashboard">
      <div className="page-header">
        <h1>XRD Analysis Dashboard</h1>
        <button className="btn btn-primary" onClick={handleQuickUpload}>
          + New Analysis
        </button>
      </div>

      {/* Stats row */}
      <div className="stats-row">
        <StatCard label="Total Analyses" value={recentResults.length} icon="🔬" />
        <StatCard
          label="Avg Confidence"
          value={
            recentResults.length
              ? `${(
                  recentResults.reduce((s, r) => s + (r.confidence_score || 0), 0) /
                  recentResults.length
                ).toFixed(1)}%`
              : "—"
          }
          icon="%"
        />
        <StatCard
          label="Last Compound"
          value={recentResults[0]?.compound_name || "—"}
          icon="⚗️"
        />
      </div>

      {/* Recent results */}
      <section className="section">
        <h2>Recent Analyses</h2>
        {loading ? (
          <p className="muted">Loading…</p>
        ) : recentResults.length === 0 ? (
          <div className="empty-state">
            <p>No analyses yet.</p>
            <button className="btn btn-secondary" onClick={handleQuickUpload}>
              Upload your first CSV
            </button>
          </div>
        ) : (
          <div className="card-grid">
            {recentResults.map((r) => (
              <AnalysisSummary
                key={r.file_id}
                result={r}
                onClick={() => navigate(`/results/${r.file_id}`)}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function StatCard({ label, value, icon }) {
  return (
    <div className="stat-card">
      <span className="stat-icon">{icon}</span>
      <div>
        <div className="stat-value">{value}</div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  );
}