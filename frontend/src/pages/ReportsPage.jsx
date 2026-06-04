import React from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { analysisApi } from "../api/analysisApi";
import { toast } from "react-toastify";
import ReportDownload from "../components/ReportDownload";

/**
 * Reports Page
 * ============
 * Lists all analyses that have a completed PDF report available,
 * with per-row download and delete buttons.
 */
export default function ReportsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Fetch up to 50 recent reports from the real SQLite database
  const { data: reports = [], isLoading } = useQuery({
    queryKey: ["analysisHistory"],
    queryFn: () => analysisApi.getRecentHistory(50),
  });

  // Setup the Delete Action
  const deleteMutation = useMutation({
    mutationFn: (fileId) => analysisApi.deleteAnalysis(fileId),
    onSuccess: () => {
      toast.success("Analysis deleted successfully.");
      // Instantly refresh the list so the deleted row disappears
      queryClient.invalidateQueries(["analysisHistory"]);
    },
    onError: (error) => {
      console.error(error);
      toast.error("Failed to delete analysis.");
    }
  });

  const handleDelete = (fileId) => {
    // Safety check so users don't accidentally delete data
    if (window.confirm("Are you sure you want to permanently delete this analysis?")) {
      deleteMutation.mutate(fileId);
    }
  };

  if (isLoading) {
    return <div className="page reports-page"><div className="page-loader">Loading reports…</div></div>;
  }

  return (
    <div className="page reports-page">
      <div className="page-header">
        <h1>Reports</h1>
        <p className="subtitle">Download PDF reports or manage completed analyses.</p>
      </div>

      {reports.length === 0 ? (
        <div className="empty-state" style={{ textAlign: "center", padding: "40px", backgroundColor: "#f9fafb", borderRadius: "8px", border: "1px dashed #d1d5db" }}>
          <p style={{ color: "#6b7280", marginBottom: "15px" }}>No completed analyses found in the database.</p>
          <button className="btn btn-primary" onClick={() => navigate("/upload")}>
            Start a new analysis
          </button>
        </div>
      ) : (
        <div className="reports-list" style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
          {reports.map((r) => (
            <div 
              key={r.file_id} 
              style={{ 
                display: "flex", 
                alignItems: "center", 
                gap: "15px", 
                backgroundColor: "#ffffff", 
                padding: "15px", 
                borderRadius: "8px", 
                border: "1px solid #e5e7eb",
                boxShadow: "0 1px 3px 0 rgba(0,0,0,0.05)"
              }}
            >
              {/* Report Details Wrapper */}
              <div style={{ flex: 1 }}>
                <ReportDownload result={r} />
              </div>
              
              {/* Delete Button */}
              <button
                onClick={() => handleDelete(r.file_id)}
                disabled={deleteMutation.isLoading}
                style={{
                  padding: "8px 12px",
                  backgroundColor: "#fee2e2",
                  color: "#dc2626",
                  border: "1px solid #fecaca",
                  borderRadius: "6px",
                  cursor: "pointer",
                  fontWeight: "600",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  opacity: deleteMutation.isLoading ? 0.6 : 1
                }}
              >
                🗑️ Delete
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}