import React from "react";

/**
 * PeakTable Component
 * ===================
 * Displays tabular numeric evaluation fields for matched reflections.
 * Highlights exactly which phase and polytype variation each experimental peak maps to.
 */
export default function PeakTable({ peaks = [] }) {
  if (!peaks || peaks.length === 0) {
    return (
      <div
        style={{
          padding: "30px 20px",
          textAlign: "center",
          backgroundColor: "#f9fafb",
          borderRadius: "6px",
          border: "1px dashed #d1d5db",
          color: "#4b5563",
          fontFamily: "Inter, sans-serif"
        }}
      >
        <p style={{ margin: 0, fontWeight: "600", fontSize: "15px" }}>
          ℹ️ No Crystal Card Matches Found
        </p>
        <p style={{ margin: "4px 0 0 0", fontSize: "13px", color: "#6b7280" }}>
          This sample profile displays an amorphous background or disordered precursor scattering matrix.
          No discrete Bragg reflections match the standard crystalline database.
        </p>
      </div>
    );
  }

  // UPGRADE: Accept both arguments to look up polytype strings for accurate style mapping
  const getPhaseBadgeStyle = (phaseName = "", polytype = "") => {
    const nameLower = phaseName.toLowerCase();
    const polyLower = polytype.toLowerCase();

    // 1. Cubic Phase Categories (3C)
    const isCubic = nameLower.includes("3c") || nameLower.includes("cubic") || 
                    polyLower.includes("3c") || polyLower.includes("cubic");

    // 2. Hexagonal Phase Categories (2H, 4H, 6H)
    const isHex = nameLower.includes("6h") || nameLower.includes("4h") || nameLower.includes("2h") || nameLower.includes("hexagonal") ||
                  polyLower.includes("6h") || polyLower.includes("4h") || polyLower.includes("2h") || polyLower.includes("hexagonal");

    // 3. Rhombohedral Phase Categories (15R, 3R)
    const isRhombo = nameLower.includes("15r") || nameLower.includes("3r") || nameLower.includes("rhombohedral") ||
                     polyLower.includes("15r") || polyLower.includes("3r") || polyLower.includes("rhombohedral");

    if (isCubic) {
      return {
        padding: "4px 10px", borderRadius: "4px", fontSize: "12px", fontWeight: "700", display: "inline-block",
        backgroundColor: "#eff6ff", color: "#1e40af", border: "1px solid #bfdbfe",
      };
    }
    if (isHex) {
      return {
        padding: "4px 10px", borderRadius: "4px", fontSize: "12px", fontWeight: "700", display: "inline-block",
        backgroundColor: "#f0fdf4", color: "#166534", border: "1px solid #bbf7d0",
      };
    }
    if (isRhombo) {
      return {
        padding: "4px 10px", borderRadius: "4px", fontSize: "12px", fontWeight: "700", display: "inline-block",
        backgroundColor: "#f5f3ff", color: "#5b21b6", border: "1px solid #ddd6fe", // Sharp purple styling for rhombohedral cards
      };
    }

    // Default Fallback
    return {
      padding: "4px 10px", borderRadius: "4px", fontSize: "12px", fontWeight: "700", display: "inline-block",
      backgroundColor: "#f3f4f6", color: "#374151", border: "1px solid #e5e7eb",
    };
  };

  return (
    <div style={{ overflowX: "auto", width: "100%", marginTop: "10px" }}>
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          textAlign: "left",
          fontSize: "14px",
          fontFamily: "Inter, sans-serif"
        }}
      >
        <thead>
          <tr style={{ backgroundColor: "#f9fafb", borderBottom: "2px solid #e5e7eb" }}>
            <th style={{ padding: "12px 16px", color: "#374151", fontWeight: "600" }}>Assigned Phase</th>
            <th style={{ padding: "12px 16px", color: "#374151", fontWeight: "600" }}>2θ Exp (°)</th>
            <th style={{ padding: "12px 16px", color: "#374151", fontWeight: "600" }}>2θ Std (°)</th>
            <th style={{ padding: "12px 16px", color: "#374151", fontWeight: "600" }}>Δ2θ (°)</th>
            <th style={{ padding: "12px 16px", color: "#374151", fontWeight: "600" }}>d-spacing (Å)</th>
            <th style={{ padding: "12px 16px", color: "#374151", fontWeight: "600" }}>Std I (%)</th>
            <th style={{ padding: "12px 16px", color: "#374151", fontWeight: "600" }}>(h k l) Plane</th>
          </tr>
        </thead>
        <tbody>
          {peaks.map((peak, idx) => {
            const twoThetaExp = peak.two_theta_exp != null ? Number(peak.two_theta_exp) : 0;
            const twoThetaStd = peak.two_theta_std != null ? Number(peak.two_theta_std) : 0;
            const deltaTwoTheta = peak.delta_two_theta != null ? Number(peak.delta_two_theta) : 0;
            const dSpacing = peak.d_spacing != null ? Number(peak.d_spacing) : 0;
            const intensityStd = peak.intensity_std != null ? Number(peak.intensity_std) : 0;
            const currentPolytype = peak.polytype || "";

            return (
              <tr
                key={`${twoThetaExp}-${idx}`}
                style={{
                  borderBottom: "1px solid #e5e7eb",
                  backgroundColor: idx % 2 === 0 ? "#ffffff" : "#f9fafb"
                }}
              >
                <td style={{ padding: "12px 16px" }}>
                  {/* UPGRADE: Forward polytype value down to color map rules */}
                  <span style={getPhaseBadgeStyle(peak.phase_name, currentPolytype)}>
                    {peak.phase_name || "Unassigned Matrix"}
                    {currentPolytype ? ` (${currentPolytype})` : ""}
                  </span>
                </td>
                <td style={{ padding: "12px 16px", fontWeight: "500", color: "#111827" }}>
                  {twoThetaExp.toFixed(4)}
                </td>
                <td style={{ padding: "12px 16px", color: "#4b5563" }}>
                  {twoThetaStd.toFixed(4)}
                </td>
                <td
                  style={{
                    padding: "12px 16px",
                    fontWeight: "600",
                    color: Math.abs(deltaTwoTheta) > 0.05 ? "#dc2626" : "#16a34a"
                  }}
                >
                  {deltaTwoTheta > 0 ? "+" : ""}
                  {deltaTwoTheta.toFixed(4)}
                </td>
                <td style={{ padding: "12px 16px", color: "#4b5563", fontFamily: "Courier, monospace" }}>
                  {dSpacing.toFixed(4)}
                </td>
                <td style={{ padding: "12px 16px", color: "#4b5563" }}>
                  {intensityStd.toFixed(1)}%
                </td>
                <td style={{ padding: "12px 16px", fontWeight: "700", color: "#4b5563" }}>
                  ({peak.h} {peak.k} {peak.l})
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}