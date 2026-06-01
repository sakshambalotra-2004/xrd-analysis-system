import React from "react";

/**
 * CrystalInfo
 * ===========
 * Detailed crystallographic property panel shown on the Analysis page.
 */
export default function CrystalInfo({
  compoundName,
  formula,
  crystalSystem,
  spaceGroup,
  crystalliteSizeNm,
  meanPeakShift,
  strainIndicator,
  detectedPhases = [],
  confidenceScore,
}) {
  const strainClass =
    strainIndicator === "Tensile"
      ? "badge--tensile"
      : strainIndicator === "Compressive"
      ? "badge--compressive"
      : "badge--none";

  return (
    <div className="card crystal-info">
      <h3>Crystal Information</h3>
      <table className="info-table">
        <tbody>
          <tr><td>Compound</td><td><strong>{compoundName || "—"}</strong></td></tr>
          <tr><td>Formula</td><td>{formula || "—"}</td></tr>
          <tr><td>Crystal System</td><td>{crystalSystem || "—"}</td></tr>
          <tr><td>Space Group</td><td>{spaceGroup || "—"}</td></tr>
          <tr>
            <td>Crystallite Size</td>
            <td>{crystalliteSizeNm ? `${crystalliteSizeNm} nm` : "—"}</td>
          </tr>
          <tr>
            <td>Mean Peak Shift</td>
            <td>
              {meanPeakShift != null
                ? `${meanPeakShift >= 0 ? "+" : ""}${meanPeakShift.toFixed(4)}°`
                : "—"}
            </td>
          </tr>
          <tr>
            <td>Strain</td>
            <td>
              <span className={`badge ${strainClass}`}>{strainIndicator || "None"}</span>
            </td>
          </tr>
          <tr>
            <td>Confidence</td>
            <td>{confidenceScore ? `${confidenceScore.toFixed(1)}%` : "—"}</td>
          </tr>
          <tr>
            <td>Phases Detected</td>
            <td>{detectedPhases.length ? detectedPhases.join(", ") : "Single phase"}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}