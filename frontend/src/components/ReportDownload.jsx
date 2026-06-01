import React, { useState } from "react";
import { reportApi } from "../api/reportApi";

/**
 * ReportDownload
 * ==============
 * Row card shown on the Reports page for each completed analysis.
 * Displays compound info and provides PDF download functionality.
 *
 * Props
 * -----
 * result : object — analysis result containing file_id, compound_name,
 *                   formula, crystal_system, space_group,
 *                   confidence_score, crystallite_size_nm,
 *                   detected_phases, mean_peak_shift_deg
 */
export default function ReportDownload({ result = {} }) {
  const {
    file_id = "",
    compound_name = "Unknown",
    formula = "?",
    crystal_system = "—",
    space_group = "—",
    confidence_score = 0,
    crystallite_size_nm = null,
    detected_phases = [],
    mean_peak_shift_deg = null,
  } = result;

  const [downloading, setDownloading] = useState(false);

  const scoreColor =
    confidence_score >= 80
      ? "#2ca02c"
      : confidence_score >= 50
      ? "#ff7f0e"
      : "#d62728";

  const handleDownload = async () => {
    setDownloading(true);
    try {
      await reportApi.downloadPdf(file_id, `xrd_report_${formula}_${file_id.slice(0, 8)}.pdf`);
    } catch (err) {
      console.error("Download failed:", err);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="card report-row">
      {/* Left: compound information */}
      <div className="report-info">
        {/* Formula badge */}
        <span
          className="report-formula-badge"
          style={{
            background: "#e8eeff",
            color: "#1B3A6B",
            borderRadius: "6px",
            padding: "4px 10px",
            fontWeight: 800,
            fontSize: "16px",
            minWidth: "48px",
            textAlign: "center",
          }}
        >
          {formula}
        </span>

        {/* Compound name + meta */}
        <div style={{ flex: 1 }}>
          <div className="report-compound">{compound_name}</div>
          <div
            style={{
              display: "flex",
              gap: "12px",
              marginTop: "3px",
              fontSize: "12px",
              color: "#6c757d",
              flexWrap: "wrap",
            }}
          >
            <span>{crystal_system}</span>
            <span>·</span>
            <span>{space_group}</span>
            {crystallite_size_nm != null && (
              <>
                <span>·</span>
                <span>{crystallite_size_nm} nm</span>
              </>
            )}
            {mean_peak_shift_deg != null && (
              <>
                <span>·</span>
                <span>
                  Δ2θ {mean_peak_shift_deg >= 0 ? "+" : ""}
                  {mean_peak_shift_deg.toFixed(4)}°
                </span>
              </>
            )}
          </div>

          {/* Multi-phase tags */}
          {detected_phases.length > 1 && (
            <div className="phase-tags" style={{ marginTop: "6px" }}>
              {detected_phases.map((p) => (
                <span key={p} className="phase-tag">
                  {p}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Confidence score */}
        <div
          style={{
            textAlign: "right",
            minWidth: "64px",
          }}
        >
          <div
            style={{
              fontSize: "20px",
              fontWeight: 800,
              color: scoreColor,
              lineHeight: 1.1,
            }}
          >
            {confidence_score.toFixed(1)}%
          </div>
          <div style={{ fontSize: "11px", color: "#6c757d" }}>confidence</div>
        </div>
      </div>

      {/* Right: action buttons */}
      <div className="report-actions" style={{ display: "flex", gap: "8px", flexShrink: 0 }}>
        {/* Open in new tab */}
        <a
          className="btn btn-secondary"
          href={reportApi.getPdfUrl(file_id)}
          target="_blank"
          rel="noreferrer"
          style={{ fontSize: "12px", padding: "6px 14px" }}
        >
          View
        </a>

        {/* Programmatic download with progress state */}
        <button
          className="btn btn-primary"
          onClick={handleDownload}
          disabled={downloading || !file_id}
          style={{ fontSize: "12px", padding: "6px 14px" }}
        >
          {downloading ? "Downloading…" : "Download PDF"}
        </button>
      </div>
    </div>
  );
}