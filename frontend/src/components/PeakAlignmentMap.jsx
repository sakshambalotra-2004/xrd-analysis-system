import React from "react";

/**
 * PeakAlignmentMap Component
 * =========================
 * Displays an explicit, side-by-side matching intersection layer showing 
 * exactly which experimental data point matched which standard card and polytype.
 */
export default function PeakAlignmentMap({ peaks = [] }) {
  if (!peaks || peaks.length === 0) {
    return <p style={{ color: "#6b7280", fontStyle: "italic" }}>No phase alignments available.</p>;
  }

  // Group matched peaks by their polytype designation dynamically
  const groupedByPolytype = peaks.reduce((groups, peak) => {
    const poly = peak.polytype || "Standard Phase (No Polytype)";
    if (!groups[poly]) groups[poly] = [];
    groups[poly].push(peak);
    return groups;
  }, {});

  return (
    <div style={{ fontFamily: "Inter, sans-serif", marginTop: "20px" }}>
      {Object.entries(groupedByPolytype).map(([polytype, matchedPeaks]) => (
        <div 
          key={polytype} 
          style={{ 
            marginBottom: "25px", 
            border: "1px solid #e5e7eb", 
            borderRadius: "8px", 
            backgroundColor: "#ffffff",
            boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.05)"
          }}
        >
          {/* Section Header displaying the active Polytype Card */}
          <div 
            style={{ 
              padding: "12px 16px", 
              backgroundColor: polytype.includes("3C") ? "#eff6ff" : polytype.includes("H") ? "#f0fdf4" : "#f5f3ff", 
              borderBottom: "1px solid #e5e7eb",
              borderTopLeftRadius: "7px",
              borderTopRightRadius: "7px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center"
            }}
          >
            <h4 style={{ margin: 0, color: "#111827", fontSize: "15px", fontWeight: "700" }}>
              Structural Polytype Group: <span style={{ color: "#2563eb" }}>{polytype}</span>
            </h4>
            <span style={{ fontSize: "12px", backgroundColor: "#ffffff", padding: "2px 8px", borderRadius: "20px", fontWeight: "600", border: "1px solid #d1d5db" }}>
              {matchedPeaks.length} Reflections Aligned
            </span>
          </div>

          {/* Side-by-Side Mapping Lists */}
          <div style={{ padding: "16px" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", gap: "12px", alignItems: "center", fontWeight: "600", fontSize: "12px", color: "#6b7280", textTransform: "uppercase", marginBottom: "8px", paddingBottom: "6px", borderBottom: "1px solid #f3f4f6" }}>
              <div>Experimental Input Data</div>
              <div>Connection</div>
              <div>Standard Card Reference</div>
            </div>

            {matchedPeaks.map((peak, idx) => {
              const exp2Theta = Number(peak.two_theta_exp || 0).toFixed(3);
              const std2Theta = Number(peak.two_theta_std || 0).toFixed(3);
              const delta = Number(peak.delta_two_theta || 0);
              const sign = delta > 0 ? "+" : "";

              return (
                <div 
                  key={idx} 
                  style={{ 
                    display: "grid", 
                    gridTemplateColumns: "1fr auto 1fr", 
                    gap: "12px", 
                    alignItems: "center", 
                    padding: "10px 0",
                    borderBottom: idx === matchedPeaks.length - 1 ? "none" : "1px solid #f9fafb"
                  }}
                >
                  {/* Left Node: Experimental Data */}
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#ef4444" }}></div>
                    <div>
                      <span style={{ fontWeight: "700", color: "#111827", fontSize: "14px" }}>{exp2Theta}°</span> 2θ
                      <div style={{ fontSize: "12px", color: "#6b7280" }}>Observed Bragg Reflection</div>
                    </div>
                  </div>

                  {/* Middle Node: Aligned Connector Arrow with Delta */}
                  <div style={{ textAlign: "center", minWidth: "90px" }}>
                    <div style={{ fontSize: "11px", fontWeight: "700", color: Math.abs(delta) > 0.04 ? "#dc2626" : "#16a34a", backgroundColor: Math.abs(delta) > 0.04 ? "#fee2e2" : "#dcfce7", padding: "1px 6px", borderRadius: "4px", display: "inline-block" }}>
                      Δ2θ: {sign}{delta.toFixed(4)}°
                    </div>
                    <div style={{ color: "#d1d5db", fontSize: "14px", marginTop: "-2px" }}>──────►</div>
                  </div>

                  {/* Right Node: Reference Database Card Standard */}
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", justifyContent: "space-between" }}>
                    <div>
                      <span style={{ fontWeight: "700", color: "#166534", fontSize: "14px" }}>{std2Theta}°</span> 2θ
                      <div style={{ fontSize: "12px", color: "#4b5563" }}>({peak.h} {peak.k} {peak.l}) Miller Plane</div>
                    </div>
                    <div style={{ fontSize: "11px", color: "#9ca3af", fontStyle: "italic" }}>
                      {peak.phase_name}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}