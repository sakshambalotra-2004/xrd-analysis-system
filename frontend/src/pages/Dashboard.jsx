import React from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { analysisApi } from "../api/analysisApi";
import AnalysisSummary from "../components/AnalysisSummary";

export default function Dashboard() {
  const navigate = useNavigate();

  // 1. Fetch real history from the SQLite backend using React Query!
  const { data: recentResults = [], isLoading } = useQuery({
    queryKey: ["analysisHistory"],
    queryFn: () => analysisApi.getRecentHistory(5),
  });

  const handleQuickUpload = () => navigate("/upload");

  // Format the Last Compound to include the Polytype
  const lastResult = recentResults[0];
  const lastCompoundDisplay = lastResult
    ? `${lastResult.compound_name || "Unknown"}${lastResult.polytype ? ` (${lastResult.polytype})` : ""}`
    : "—";

  return (
    <div className="page dashboard">
      <div className="page-header">
        <h1>XRD Analysis Dashboard</h1>
        <button className="btn btn-primary" onClick={handleQuickUpload}>
          + New Analysis
        </button>
      </div>

      {/* Stats row */}
      <div className="stats-row" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "20px", marginBottom: "30px" }}>
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
          icon="📊"
        />
        <StatCard
          label="Last Phase Detected"
          value={lastCompoundDisplay}
          icon="⚗️"
        />
      </div>

      {/* Recent results */}
      <section className="section">
        <h2>Database History</h2>
        {isLoading ? (
          <p className="muted">Fetching real-time data from database…</p>
        ) : recentResults.length === 0 ? (
          <div className="empty-state" style={{ textAlign: "center", padding: "40px", backgroundColor: "#f9fafb", borderRadius: "8px", border: "1px dashed #d1d5db" }}>
            <p style={{ color: "#6b7280", marginBottom: "15px" }}>Your database is currently empty.</p>
            <button className="btn btn-secondary" onClick={handleQuickUpload}>
              Upload your first CSV
            </button>
          </div>
        ) : (
          <div className="card-grid" style={{ display: "grid", gap: "20px" }}>
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
    <div className="stat-card" style={{ display: "flex", alignItems: "center", gap: "15px", padding: "20px", backgroundColor: "#ffffff", borderRadius: "8px", boxShadow: "0 1px 3px 0 rgba(0,0,0,0.1)", border: "1px solid #e5e7eb" }}>
      <div style={{ fontSize: "28px", backgroundColor: "#f3f4f6", width: "50px", height: "50px", display: "flex", alignItems: "center", justifyContent: "center", borderRadius: "50%" }}>
        {icon}
      </div>
      <div>
        <div style={{ fontSize: "20px", fontWeight: "700", color: "#111827" }}>{value}</div>
        <div style={{ fontSize: "13px", color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.05em", marginTop: "2px" }}>{label}</div>
      </div>
    </div>
  );
}