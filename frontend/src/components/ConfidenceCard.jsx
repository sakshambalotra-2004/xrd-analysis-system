import React from "react";

/**
 * ConfidenceCard
 * ==============
 * Displays the primary compound identification result and confidence score
 * as a prominent summary card.
 */
export function ConfidenceCard({
  compoundName,
  formula,
  crystalSystem,
  spaceGroup,
  confidenceScore,
  detectedPhases = [],
}) {
  const barColor =
    confidenceScore >= 80 ? "#2ca02c" : confidenceScore >= 50 ? "#ff7f0e" : "#d62728";

  return (
    <div className="card confidence-card">
      <div className="confidence-header">
        <h3>Best Match Result</h3>
        <span className="confidence-score" style={{ color: barColor }}>
          {confidenceScore?.toFixed(1)}%
        </span>
      </div>

      <table className="info-table">
        <tbody>
          <tr><td>Compound</td><td><strong>{compoundName}</strong></td></tr>
          <tr><td>Formula</td><td>{formula}</td></tr>
          <tr><td>Crystal System</td><td>{crystalSystem}</td></tr>
          <tr><td>Space Group</td><td>{spaceGroup}</td></tr>
        </tbody>
      </table>

      {/* Confidence bar */}
      <div className="confidence-bar-wrap">
        <div
          className="confidence-bar"
          style={{ width: `${confidenceScore}%`, background: barColor }}
        />
      </div>

      {/* FIXED: Added 'idx' to the map loop to create unique keys and prevent console warnings */}
      {detectedPhases.length > 1 && (
        <div className="phase-tags">
          {detectedPhases.map((p, idx) => (
            <span key={`${p}-${idx}`} className="phase-tag">
              {p}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default ConfidenceCard;