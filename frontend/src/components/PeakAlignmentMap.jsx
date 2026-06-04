import React from "react";

/**
 * PeakAlignmentMap Component
 * =========================
 * Displays an explicit, side-by-side matching intersection layer showing 
 * exactly which experimental data point matched which standard card and polytype.
 */
export default function PeakAlignmentMap({ peaks = [] }) {
  if (!peaks || peaks.length === 0) return null;

  // 1. Group matched peaks by both compound name AND polytype
  const grouped = peaks.reduce((acc, peak) => {
    const poly = peak.polytype || "Standard";
    const key = `${peak.phase_name} (${poly})`;
    if (!acc[key]) acc[key] = [];
    acc[key].push(peak);
    return acc;
  }, {});

  return (
    <div style={{ fontFamily: "Inter, sans-serif", marginTop: "20px" }}>
      {Object.entries(grouped).map(([groupKey, matchedPeaks]) => (
        <div 
          key={groupKey} 
          style={{ 
            marginBottom: "25px", 
            border: "1px solid #e5e7eb", 
            borderRadius: "8px", 
            backgroundColor: "#ffffff",
            boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.05)"
          }}
        >
          {/* Section Header */}
          <div 
            style={{ 
              padding: "12px 16px", 
              backgroundColor: "#f9fafb", 
              borderBottom: "1px solid #e5e7eb",
              borderTopLeftRadius: "7px",
              borderTopRightRadius: "7px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center"
            }}
          >
            <h4 style={{ margin: 0, color: "#111827", fontSize: "15px", fontWeight: "700" }}>
              Structural Alignment: <span style={{ color: "#2563eb" }}>{groupKey}</span>
            </h4>
            <span style={{ fontSize: "12px", backgroundColor: "#ffffff", padding: "2px 8px", borderRadius: "20px", fontWeight: "600", border: "1px solid #d1d5db" }}>
              {matchedPeaks.length} Reflections
            </span>
          </div>

          {/* Mapping Grid */}
          <div style={{ padding: "16px" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", gap: "12px", fontWeight: "600", fontSize: "12px", color: "#6b7280", textTransform: "uppercase", marginBottom: "8px", paddingBottom: "6px", borderBottom: "1px solid #f3f4f6" }}>
              <div>Experimental Input</div>
              <div>Alignment</div>
              <div>Standard Reference</div>
            </div>

            {matchedPeaks.map((peak, idx) => {
              const delta = Number(peak.delta_two_theta || 0);
              return (
                <div 
                  key={`${peak.two_theta_std}-${idx}`} 
                  style={{ 
                    display: "grid", 
                    gridTemplateColumns: "1fr auto 1fr", 
                    gap: "12px", 
                    alignItems: "center", 
                    padding: "10px 0",
                    borderBottom: idx === matchedPeaks.length - 1 ? "none" : "1px solid #f9fafb"
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#ef4444" }}></div>
                    <div>
                      <span style={{ fontWeight: "700" }}>{Number(peak.two_theta_exp).toFixed(3)}°</span>
                    </div>
                  </div>

                  <div style={{ textAlign: "center", minWidth: "80px" }}>
                    <div style={{ fontSize: "11px", fontWeight: "700", color: Math.abs(delta) > 0.05 ? "#dc2626" : "#16a34a", padding: "2px 6px", borderRadius: "4px", backgroundColor: "#f3f4f6" }}>
                      Δ {delta > 0 ? "+" : ""}{delta.toFixed(3)}°
                    </div>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: "8px" }}>
                    <div style={{ textAlign: "right" }}>
                      <span style={{ fontWeight: "700", color: "#166534" }}>{Number(peak.two_theta_std).toFixed(3)}°</span>
                      <div style={{ fontSize: "11px", color: "#6b7280" }}>({peak.h} {peak.k} {peak.l})</div>
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