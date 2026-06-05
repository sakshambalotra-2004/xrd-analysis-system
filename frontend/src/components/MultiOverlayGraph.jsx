import React, { useState, useCallback, useMemo } from "react";
import Plot from "react-plotly.js";

// ============================================================================
// 1. CONSTANTS & PALETTE
// ============================================================================

const PALETTE = [
  { stroke: "#1a6fc4", fill: "rgba(26,111,196,0.07)" },
  { stroke: "#c45c1a", fill: "rgba(196,92,26,0.07)" },
  { stroke: "#1a9c62", fill: "rgba(26,156,98,0.07)" },
];

// ============================================================================
// 2. HELPER COMPONENTS
// ============================================================================

function StatBadge({ label, value, color }) {
  return (
    <div style={badgeStyles.wrap}>
      <span style={{ ...badgeStyles.dot, background: color }} />
      <span style={badgeStyles.label}>{label}</span>
      <span style={{ ...badgeStyles.val, color }}>{value}</span>
    </div>
  );
}

// ============================================================================
// 3. DATA PROCESSING
// ============================================================================

function computeStats(dataset) {
  if (!dataset?.intensity?.length) return null;

  const intensities = dataset.intensity;
  const angles = dataset.twoTheta;
  
  const maxIntensity = Math.max(...intensities);
  const maxIndex = intensities.indexOf(maxIntensity);
  const mean = intensities.reduce((sum, val) => sum + val, 0) / intensities.length;
  
  const snr = maxIntensity / (mean || 1);
  const range = angles ? `${angles[0]?.toFixed(2)}° – ${angles[angles.length - 1]?.toFixed(2)}°` : "—";
  const peak = angles ? `${angles[maxIndex]?.toFixed(3)}°` : "—";
  
  return { snr, range, peak };
}

// ============================================================================
// 4. MAIN COMPONENT
// ============================================================================

export default function MultiOverlayGraph({ datasets = [] }) {
  // Toolbar State
  const [offsetMode, setOffsetMode] = useState(false);
  const [normalise, setNormalise]   = useState(false);
  const [showFill, setShowFill]     = useState(false);
  const [logScale, setLogScale]     = useState(false);

  // Memoize the Plotly traces so they only recalculate when data or toggles change
  const traces = useMemo(() => {
    if (!datasets.length) return [];

    return datasets.map((dataset, index) => {
      const colorPalette = PALETTE[index % PALETTE.length];
      let activeIntensity = dataset.intensity ? [...dataset.intensity] : [];

      // Handle Normalisation
      if (normalise && activeIntensity.length) {
        const absoluteMax = Math.max(...activeIntensity);
        activeIntensity = activeIntensity.map(val => absoluteMax ? val / absoluteMax : val);
      }

      // Handle Vertical Y-Offset (Cascading graph effect)
      let yOffset = 0;
      if (offsetMode && index > 0) {
        const offsetMultiplier = normalise ? 1 : Math.max(...(datasets[0]?.intensity || [1]));
        yOffset = index * 1.2 * offsetMultiplier;
      }

      const finalYValues = activeIntensity.map(val => val + yOffset);

      // Construct base Plotly trace object
      const baseTrace = {
        x: dataset.twoTheta,
        y: finalYValues,
        type: "scatter",
        mode: "lines",
        name: dataset.name || `Scan ${index + 1}`,
        line: { color: colorPalette.stroke, width: 2.5 }, // Bolder lines
        hovertemplate: `<b>${dataset.name || `Scan ${index + 1}`}</b><br>2θ = %{x:.3f}°<br>I = %{y:.1f} a.u.<extra></extra>`,
      };

      // Apply area fill if toggled
      if (showFill) {
        baseTrace.fill = "tozeroy";
        baseTrace.fillcolor = colorPalette.fill;
      }

      return baseTrace;
    });
  }, [datasets, offsetMode, normalise, showFill]);

  // Handler: Export CSV Data
  const handleExportCSV = useCallback(() => {
    if (!datasets.length) return;

    const headerRow = ["2theta", ...datasets.map(d => d.name || "scan")].join(",");
    
    const dataRows = (datasets[0]?.twoTheta || []).map((theta, idx) => {
      const intensitiesAtTheta = datasets.map(d => (d.intensity?.[idx] ?? "").toString());
      return [theta, ...intensitiesAtTheta].join(",");
    });

    const csvContent = [headerRow, ...dataRows].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    
    // Trigger download
    const link = document.createElement("a");
    Object.assign(link, { href: url, download: "XRD_overlay_data.csv" });
    link.click();
    URL.revokeObjectURL(url);
  }, [datasets]);

  // Empty State Rendering
  if (!datasets.length) {
    return (
      <div style={graphStyles.empty}>
        <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="#b0bec8" strokeWidth="2">
          <path d="M3 3v18h18"/><path d="M7 16l4-7 4 4 3-6"/>
        </svg>
        <p style={graphStyles.emptyText}>SELECT SCANS TO OVERLAY</p>
      </div>
    );
  }

  return (
    <div style={graphStyles.root}>
      
      {/* ── Toolbar ── */}
      <div style={graphStyles.toolbar}>
        <span style={graphStyles.toolbarTitle}>DIFFRACTOGRAM OVERLAY</span>
        
        <div style={graphStyles.controls}>
          {/* Dynamic Toggle Buttons */}
          {[
            { label: "OFFSET", state: offsetMode, set: setOffsetMode },
            { label: "NORM.",  state: normalise,  set: setNormalise  },
            { label: "FILL",   state: showFill,   set: setShowFill   },
            { label: "LOG Y",  state: logScale,   set: setLogScale   },
          ].map(({ label, state, set }) => (
            <button 
              key={label} 
              onClick={() => set(prev => !prev)}
              style={{ ...graphStyles.btn, ...(state ? graphStyles.btnActive : {}) }}
            >
              {label}
            </button>
          ))}
          
          <div style={graphStyles.divider} />
          
          <button onClick={handleExportCSV} style={graphStyles.btn} title="Export raw data as CSV">
            ↓ CSV
          </button>
        </div>
      </div>

      {/* ── Stats Strip ── */}
      <div style={graphStyles.statsRow}>
        {datasets.map((dataset, index) => {
          const stats = computeStats(dataset);
          const color = PALETTE[index % PALETTE.length].stroke;
          
          if (!stats) return null;
          
          return (
            <React.Fragment key={index}>
              <StatBadge label={`[${index + 1}] Peak`} value={stats.peak} color={color} />
              <StatBadge label="SNR" value={stats.snr.toFixed(1)} color={color} />
              <StatBadge label="Range" value={stats.range} color={color} />
            </React.Fragment>
          );
        })}
      </div>

      {/* ── Plotly Canvas ── */}
      <div id="mog-plot" style={{ width: "100%", background: "#fff" }}>
        <Plot
          data={traces}
          layout={{
            autosize: true,
            margin: { l: 68, r: 24, t: 16, b: 56 },
            xaxis: {
              title: { text: "2θ (°)", font: { size: 13, color: "#1e2d3d", family: "JetBrains Mono", weight: "bold" } },
              zeroline: false, 
              showgrid: true,
              gridcolor: "#edf0f4", 
              gridwidth: 2, // Bolder grid
              tickfont: { size: 12, color: "#4a5568", family: "JetBrains Mono", weight: "bold" },
              linecolor: "#aab4be", 
              tickcolor: "#aab4be", 
              mirror: true,
            },
            yaxis: {
              title: {
                text: normalise ? "Normalised Intensity" : "Intensity (a.u.)",
                font: { size: 13, color: "#1e2d3d", family: "JetBrains Mono", weight: "bold" },
              },
              type: logScale ? "log" : "linear",
              zeroline: false, 
              showgrid: true,
              gridcolor: "#edf0f4", 
              gridwidth: 2, // Bolder grid
              tickfont: { size: 12, color: "#4a5568", family: "JetBrains Mono", weight: "bold" },
              linecolor: "#aab4be", 
              tickcolor: "#aab4be",
              mirror: true, 
              exponentformat: "SI",
            },
            legend: {
              orientation: "h", 
              yanchor: "bottom", 
              y: 1.02,
              xanchor: "left", 
              x: 0,
              font: { size: 12, color: "#1e2d3d", family: "JetBrains Mono", weight: "bold" },
              bgcolor: "rgba(255,255,255,0)",
              bordercolor: "#dde3ea", 
              borderwidth: 2, // Bolder legend border
            },
            paper_bgcolor: "#ffffff",
            plot_bgcolor:  "#ffffff",
            hovermode: "x unified",
            hoverlabel: {
              bgcolor: "#1e2d3d", 
              bordercolor: "#3a4d5e",
              font: { size: 13, color: "#e8f0f8", family: "JetBrains Mono", weight: "bold" },
            },
            dragmode: "zoom",
          }}
          useResizeHandler
          style={{ width: "100%", height: 460 }}
          config={{
            responsive: true,
            scrollZoom: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ["select2d", "lasso2d", "autoScale2d"],
            toImageButtonOptions: {
              format: "png", 
              filename: "XRD_overlay",
              width: 2400, 
              height: 1200, 
              scale: 2,
            },
          }}
        />
      </div>

      {/* ── Footer note ── */}
      <div style={graphStyles.axisNote}>
        Cu Kα radiation (λ = 1.5406 Å) · Data shown as-collected · Scroll to zoom · Drag to pan
      </div>
      
    </div>
  );
}

// ============================================================================
// 5. STYLES
// ============================================================================

const badgeStyles = {
  wrap: {
    display: "flex", 
    alignItems: "center", 
    gap: 6,
    padding: "3px 10px", 
    borderRadius: 4,
    background: "#f4f6f8", 
    border: "2px solid #dde3ea", // Bolder border
  },
  dot: { 
    width: 8, // Slightly larger
    height: 8, 
    borderRadius: "50%", 
    flexShrink: 0 
  },
  label: { 
    fontSize: 11, 
    fontWeight: 700, // Bolder
    color: "#6b7a8a", 
    fontFamily: "'JetBrains Mono', monospace", 
    letterSpacing: "0.05em" 
  },
  val: { 
    fontSize: 12, 
    fontFamily: "'JetBrains Mono', monospace", 
    fontWeight: 900, // Extra Bold
    marginLeft: 3 
  },
};

const graphStyles = {
  root: {
    background: "#fff",
    border: "2px solid #dde3ea", // Bolder border
    borderRadius: 7,
    overflow: "hidden",
    display: "flex",
    flexDirection: "column",
  },
  empty: {
    display: "flex", 
    flexDirection: "column",
    alignItems: "center", 
    justifyContent: "center",
    minHeight: 340,
    background: "#f8fafc",
    border: "2px solid #dde3ea", // Bolder border
    borderRadius: 7,
  },
  emptyText: {
    margin: "10px 0 0", 
    color: "#7a8a99", 
    fontWeight: 800, // Bolder
    fontSize: 13, 
    fontFamily: "'JetBrains Mono', monospace", 
    letterSpacing: "0.08em"
  },
  toolbar: {
    display: "flex", 
    alignItems: "center",
    justifyContent: "space-between",
    padding: "8px 14px",
    borderBottom: "2px solid #dde3ea", // Bolder border
    background: "#f4f6f8",
    flexWrap: "wrap", 
    gap: 8,
  },
  toolbarTitle: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 12, 
    letterSpacing: "0.12em",
    color: "#1a6fc4", 
    fontWeight: 900, // Extra Bold
  },
  controls: { 
    display: "flex", 
    alignItems: "center", 
    gap: 5, 
    flexWrap: "wrap" 
  },
  btn: {
    padding: "4px 10px", 
    fontSize: 11,
    fontWeight: 800, // Bolder
    fontFamily: "'JetBrains Mono', monospace",
    letterSpacing: "0.07em",
    background: "#fff",
    border: "2px solid #ccd3dc", // Bolder border
    borderRadius: 4, 
    color: "#4a5568",
    cursor: "pointer", 
    transition: "all 0.15s",
  },
  btnActive: {
    background: "rgba(26,111,196,0.08)",
    borderColor: "#1a6fc4", 
    color: "#1a6fc4",
  },
  divider: { 
    width: 2, // Bolder divider
    height: 16, 
    background: "#dde3ea", 
    margin: "0 5px" 
  },
  statsRow: {
    display: "flex", 
    flexWrap: "wrap", 
    gap: 6,
    padding: "7px 14px",
    borderBottom: "2px solid #dde3ea", // Bolder border
    background: "#f9fafb",
  },
  axisNote: {
    padding: "6px 14px", 
    fontSize: 11,
    fontWeight: 600, // Bolder
    fontFamily: "'JetBrains Mono', monospace",
    color: "#7a8a99", 
    letterSpacing: "0.04em",
    borderTop: "2px solid #dde3ea", // Bolder border
    background: "#f9fafb",
  },
};