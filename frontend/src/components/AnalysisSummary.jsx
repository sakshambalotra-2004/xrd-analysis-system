import React from "react";

/**
 * AnalysisSummary
 * ===============
 * Compact card representing one completed XRD analysis run.
 * Used on the Dashboard to list recent analyses.
 *
 * Props
 * -----
 * result  : object  — analysis result with compound_name, formula,
 *                     crystal_system, confidence_score,
 *                     crystallite_size_nm, detected_phases, file_id
 * onClick : func    — called when the card is clicked (navigate to results)
 */
export default function AnalysisSummary({ result = {}, onClick }) {
  const {
    compound_name = "Unknown",
    formula = "?",
    crystal_system = "—",
    confidence_score = 0,
    crystallite_size_nm = null,
    detected_phases = [],
    file_id = "",
  } = result;

  const scoreColor =
    confidence_score >= 80
      ? "#2ca02c"
      : confidence_score >= 50
      ? "#ff7f0e"
      : "#d62728";

  return (
    <div
      className="card analysis-summary-card"
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick?.()}
      aria-label={`View results for ${compound_name}`}
    >
      {/* Header row: formula + confidence score */}
      <div className="summary-header">
        <span className="summary-formula">{formula}</span>
        <span className="summary-score" style={{ color: scoreColor }}>
          {confidence_score.toFixed(1)}%
        </span>
      </div>

      {/* Compound name */}
      <div className="summary-name" title={compound_name}>
        {compound_name}
      </div>

      {/* Meta row: crystal system + crystallite size */}
      <div className="summary-meta">
        <span>{crystal_system}</span>
        {crystallite_size_nm != null && (
          <>
            <span className="muted">·</span>
            <span>{crystallite_size_nm} nm</span>
          </>
        )}
      </div>

      {/* Multi-phase tags (shown only when more than one phase detected) */}
      {detected_phases.length > 1 && (
        <div className="phase-tags" style={{ marginTop: "8px" }}>
          {detected_phases.map((p) => (
            <span key={p} className="phase-tag">
              {p}
            </span>
          ))}
        </div>
      )}

      {/* Confidence progress bar */}
      <div
        style={{
          marginTop: "10px",
          height: "4px",
          background: "#e9ecef",
          borderRadius: "2px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${Math.min(confidence_score, 100)}%`,
            height: "100%",
            background: scoreColor,
            borderRadius: "2px",
            transition: "width 0.4s ease",
          }}
        />
      </div>
    </div>
  );
}