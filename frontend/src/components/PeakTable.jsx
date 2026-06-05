import React from "react";

export default function PeakTable({ peaks = [], rawPeaks = [] }) { 
  
  const getPhaseBadgeStyle = (phaseName = "", polytype = "") => {
    const nameLower = phaseName.toLowerCase();
    const polyLower = polytype.toLowerCase();

    const isCubic = nameLower.includes("3c") || nameLower.includes("cubic") || polyLower.includes("3c") || polyLower.includes("cubic");
    const isHex = nameLower.includes("6h") || nameLower.includes("4h") || nameLower.includes("2h") || nameLower.includes("hexagonal") || polyLower.includes("6h") || polyLower.includes("4h") || polyLower.includes("2h") || polyLower.includes("hexagonal");
    const isRhombo = nameLower.includes("15r") || nameLower.includes("3r") || nameLower.includes("rhombohedral") || polyLower.includes("15r") || polyLower.includes("3r") || polyLower.includes("rhombohedral");

    if (isCubic) return { padding: "4px 10px", borderRadius: "4px", fontSize: "12px", fontWeight: "700", display: "inline-block", backgroundColor: "#eff6ff", color: "#1e40af", border: "1px solid #bfdbfe" };
    if (isHex) return { padding: "4px 10px", borderRadius: "4px", fontSize: "12px", fontWeight: "700", display: "inline-block", backgroundColor: "#f0fdf4", color: "#166534", border: "1px solid #bbf7d0" };
    if (isRhombo) return { padding: "4px 10px", borderRadius: "4px", fontSize: "12px", fontWeight: "700", display: "inline-block", backgroundColor: "#f5f3ff", color: "#5b21b6", border: "1px solid #ddd6fe" };

    return { padding: "4px 10px", borderRadius: "4px", fontSize: "12px", fontWeight: "700", display: "inline-block", backgroundColor: "#f3f4f6", color: "#374151", border: "1px solid #e5e7eb" };
  };

  if (!peaks || peaks.length === 0) {
    return (
      <div style={{ padding: "30px 20px", textAlign: "center", backgroundColor: "#f9fafb", borderRadius: "6px", border: "1px dashed #d1d5db", color: "#4b5563" }}>
        <p style={{ margin: 0, fontWeight: "600", fontSize: "15px" }}>ℹ️ No Crystal Card Matches Found</p>
      </div>
    );
  }

  return (
    <div style={{ overflowX: "auto", width: "100%", marginTop: "10px" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "14px", fontFamily: "Inter, sans-serif" }}>
        <thead>
          <tr style={{ backgroundColor: "#f9fafb", borderBottom: "2px solid #e5e7eb" }}>
            <th style={{ padding: "12px 16px", color: "#374151", fontWeight: "600" }}>Assigned Phase</th>
            <th style={{ padding: "12px 16px", color: "#374151", fontWeight: "600" }}>2θ Exp (°)</th>
            <th style={{ padding: "12px 16px", color: "#374151", fontWeight: "600" }}>2θ Std (°)</th>
            <th style={{ padding: "12px 16px", color: "#374151", fontWeight: "600" }}>FWHM (°)</th>
            <th style={{ padding: "12px 16px", color: "#374151", fontWeight: "600" }}>Δ2θ (°)</th>
            <th style={{ padding: "12px 16px", color: "#374151", fontWeight: "600" }}>d-spacing (Å)</th>
            <th style={{ padding: "12px 16px", color: "#374151", fontWeight: "600" }}>I Std (%)</th>
            <th style={{ padding: "12px 16px", color: "#374151", fontWeight: "600" }}>(h k l)</th>
          </tr>
        </thead>
        <tbody>
          {peaks.map((peak, idx) => {
            const currentPolytype = peak.polytype || "";
            
            // CROSS-REFERENCE: Find the raw peak that matches this matched peak's 2-theta
            const matchingRawPeak = rawPeaks.find(rp => Math.abs(rp.two_theta - peak.two_theta_exp) < 0.001);
            const fwhmVal = matchingRawPeak ? matchingRawPeak.fwhm_deg : null;

            return (
              <tr key={`${peak.two_theta_exp}-${idx}`} style={{ borderBottom: "1px solid #e5e7eb", backgroundColor: idx % 2 === 0 ? "#ffffff" : "#f9fafb" }}>
                <td style={{ padding: "12px 16px" }}>
                  <span style={getPhaseBadgeStyle(peak.phase_name, currentPolytype)}>
                    {peak.phase_name || "Unassigned"}
                    {currentPolytype ? ` (${currentPolytype})` : ""}
                  </span>
                </td>
                
                <td style={{ padding: "12px 16px", fontWeight: "500", color: "#111827" }}>
                  {Number(peak.two_theta_exp).toFixed(4)}
                </td>

                <td style={{ padding: "12px 16px", color: "#4b5563" }}>
                  {peak.two_theta_std != null ? Number(peak.two_theta_std).toFixed(4) : "—"}
                </td>
                
                {/* Dynamically render the FWHM value! */}
                <td style={{ padding: "12px 16px", color: "#4f46e5", fontWeight: "700" }}>
                  {fwhmVal != null && fwhmVal > 0 ? Number(fwhmVal).toFixed(4) : "—"}
                </td>

                <td style={{ padding: "12px 16px", color: Math.abs(peak.delta_two_theta) > 0.05 ? "#dc2626" : "#16a34a", fontWeight: "600" }}>
                  {peak.delta_two_theta > 0 ? "+" : ""}{Number(peak.delta_two_theta).toFixed(4)}
                </td>
                
                <td style={{ padding: "12px 16px", color: "#4b5563", fontFamily: "Courier, monospace" }}>
                  {Number(peak.d_spacing).toFixed(4)}
                </td>

                <td style={{ padding: "12px 16px", color: "#4b5563" }}>
                  {peak.intensity_std != null ? Number(peak.intensity_std).toFixed(1) : "—"}
                </td>
                
                <td style={{ padding: "12px 16px", color: "#4b5563", fontWeight: "700" }}>
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