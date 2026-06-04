import React from "react";

/**
 * AnalysisSummary
 * ===============
 * Compact card representing one completed XRD analysis run.
 * Used on the Dashboard to list recent analyses.
 * Upgraded to append crystal polytype labels next to names and formula badges dynamically.
 *
 * Props
 * -----
 * result  : object  — analysis result with compound_name, formula, polytype,
 * crystal_system, confidence_score, crystallite_size_nm, 
 * detected_phases, file_id
 * onClick : func    — called when the card is clicked (navigate to results)
 *
 * Saksham Sharma — DRDO / BVM Project Build Execution (June 2026)
 */
export default function AnalysisSummary({ result = {}, onClick }) {
  const {
    compound_name = "Unknown",
    formula = "?",
    polytype = "", // UPGRADE: Captured explicit structural polytype parameter passed from the API response
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

  // Safely check if a polytype is present and clean it for appending
  const polytypeStr = polytype ? polytype.trim() : "";

  // Normalize detected phases array safely
  const phasesArray = Array.isArray(detected_phases)
    ? detected_phases
    : typeof detected_phases === "string"
      ? detected_phases.split(",").map((p) => p.trim())
      : [];

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
        {/* UPGRADE: Automatically stitch polytype right into the formula pill badge if present */}
        <span className="summary-formula">
          {formula}
          {polytypeStr && !formula.includes(polytypeStr) ? ` [${polytypeStr}]` : ""}
        </span>
        <span className="summary-score" style={{ color: scoreColor }}>
          {confidence_score.toFixed(1)}%
        </span>
      </div>

      {/* Compound name */}
      {/* UPGRADE: Displays name paired with polytype string directly in the card title block */}
      <div 
        className="summary-name" 
        title={polytypeStr && !compound_name.includes(polytypeStr) ? `${compound_name} (${polytypeStr})` : compound_name}
      >
        {compound_name}
        {polytypeStr && !compound_name.includes(polytypeStr) ? ` (${polytypeStr})` : ""}
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
      {phasesArray.length > 1 && (
        <div className="phase-tags" style={{ marginTop: "8px" }}>
          {phasesArray.map((p, idx) => {
            // UPGRADE: Check and verify polytype isn't duplicated inside the secondary phase tags
            const cleanTagText = polytypeStr && !p.includes(polytypeStr) && p !== "Amorphous Background Matrix"
              ? `${p} (${polytypeStr})`
              : p;

            return (
              <span key={`${p}-${idx}`} className="phase-tag">
                {cleanTagText}
              </span>
            );
          })}
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
          width: "100%"
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