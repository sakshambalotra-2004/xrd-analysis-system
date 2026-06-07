import React, { useMemo } from "react";
import Plot from "react-plotly.js";

export default function OverlayGraph({
  twoTheta = [],
  intensity = [],
  matchedPeaks = [],
  compoundName = "Standard",
  yMax = null,  // FIX: explicit ceiling from parent; avoids relying on smoothed intensity max
}) {
  const hasMatches = matchedPeaks && matchedPeaks.length > 0;

  const { scaleFactor, maxExpIntensity } = useMemo(() => {
    const maxExp = intensity.length > 0 ? Math.max(...intensity) : 1.0;
    const maxStd = hasMatches ? Math.max(...matchedPeaks.map((p) => p.intensity_std)) : 1.0;
    return { scaleFactor: maxExp / maxStd, maxExpIntensity: maxExp };
  }, [intensity, matchedPeaks, hasMatches]);

  // FIX: prefer the explicit yMax prop (computed from raw intensity in ResultsPage)
  // so the Y-axis ceiling is never clipped by smoothing artefacts
  const yAxisMax = yMax != null ? yMax : maxExpIntensity * 1.15;

  const sortedData = useMemo(() => {
    return [...twoTheta].map((x, i) => ({ x: Number(x), y: Number(intensity[i]) })).sort((a, b) => a.x - b.x);
  }, [twoTheta, intensity]);

  const sortedX = sortedData.map((p) => p.x);
  const sortedY = sortedData.map((p) => p.y);

  const data = [
    {
      x: sortedX,
      y: sortedY,
      type: "scatter",
      mode: "lines",
      name: "Experimental Profile",
      line: { color: "#000000", width: 1.2 },
      // UPGRADED to 6 decimal precision
      hovertemplate: "<b>Experimental</b><br>Angle: %{x:.6f}°<br>Intensity: %{y:.1f}<extra></extra>",
    }
  ];

  if (hasMatches) {
    data.push({
      x: matchedPeaks.map((p) => Number(p.two_theta_std)),
      y: matchedPeaks.map((p) => Number(p.intensity_std) * scaleFactor),
      type: "scatter",
      mode: "markers+text",
      name: `Standard: ${compoundName}`,
      marker: { color: "#dc2626", size: 5, symbol: "circle" },
      text: matchedPeaks.map((p) => `(${p.h} ${p.k} ${p.l})`),
      textposition: "top center",
      font: { family: "Arial, sans-serif", size: 10, color: "#dc2626" },
      // UPGRADED to 6 decimal precision
      hovertemplate: "<b>Standard</b><br>Angle: %{x:.6f}°<br>Indices: %{text}<extra></extra>",
    });
  }

  const lines = useMemo(() => {
    if (!hasMatches) return [];
    return matchedPeaks.map((p) => ({
      type: "line",
      x0: Number(p.two_theta_std), y0: 0, x1: Number(p.two_theta_std), y1: Number(p.intensity_std) * scaleFactor,
      line: { color: "#dc2626", width: 1.5, dash: "solid" },
    }));
  }, [matchedPeaks, scaleFactor, hasMatches]);

  const layout = {
    title: {
      text: hasMatches 
        ? `Phase Identification Overlay — ${compoundName}` 
        : "Amorphous Scan Profile",
      font: { size: 14, family: "Arial, sans-serif", color: "#000000", weight: "bold" },
    },
    xaxis: {
      title: { text: "Angle (°)", font: { size: 13, family: "Arial, sans-serif" } },
      ticks: "inside", ticklen: 6, tickwidth: 1.2, showline: true, linecolor: "#000000", linewidth: 1.5, mirror: "all",
    },
    yaxis: {
      title: { text: "Intensity (a.u.)", font: { size: 13, family: "Arial, sans-serif" } },
      ticks: "inside", ticklen: 6, tickwidth: 1.2, showline: true, linecolor: "#000000", linewidth: 1.5, mirror: "all",
      range: [0, yAxisMax],
      autorange: false,
    },
    shapes: lines,
    hovermode: "x unified", // Changed to 'x unified' to show both traces on hover
    legend: { x: 0.95, y: 0.95, xanchor: "right", yanchor: "top", bgcolor: "#ffffff", bordercolor: "#000000", borderwidth: 1 },
    margin: { t: 55, b: 55, l: 65, r: 35 },
    plot_bgcolor: "#ffffff", paper_bgcolor: "#ffffff",
  };

  return (
    <div className="origin-plotly-wrapper" style={{ border: "1px solid #e5e7eb", borderRadius: "6px", padding: "10px", backgroundColor: "#ffffff" }}>
      <Plot 
        data={data} 
        layout={layout} 
        useResizeHandler 
        style={{ width: "100%", height: "460px" }} 
        config={{ responsive: true, displaylogo: false, scrollZoom: true }} 
      />
    </div>
  );
}