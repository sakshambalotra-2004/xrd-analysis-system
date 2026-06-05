import React, { useMemo } from "react";
import Plot from "react-plotly.js";

export default function XRDGraph({
  twoTheta = [],
  intensity = [],
  peakPositions = [],
  title = "Experimental XRD Pattern",
  xAxisLabel = "Angle (°)",
}) {
  
  // 100% Bulletproof Intensity Mapper
  // This completely ignores the backend's peak intensity and forces the 
  // green triangle to sit exactly on the blue experimental line!
  // Replace the lockedPeakIntensities logic in XRDGraph.jsx
const lockedPeakIntensities = useMemo(() => {
  if (!twoTheta.length || !intensity.length) return [];

  return peakPositions.map((targetX) => {
    const xTarget = Number(targetX);
    
    // Find the closest point on the line
    let minDiff = Infinity;
    let closestIdx = 0;

    for (let i = 0; i < twoTheta.length; i++) {
      const diff = Math.abs(Number(twoTheta[i]) - xTarget);
      if (diff < minDiff) {
        minDiff = diff;
        closestIdx = i;
      }
    }
    
    // Only return the intensity if it's actually a valid match
    // Increase this tolerance if your peaks are still appearing at 0
    return minDiff < 0.1 ? Number(intensity[closestIdx]) : 0;
  });
}, [twoTheta, intensity, peakPositions]);

  // Ensure blue line data is strictly numerical
  const sortedData = [...twoTheta]
    .map((x, i) => ({
      x: Number(x),
      y: Number(intensity[i]),
    }))
    .sort((a, b) => a.x - b.x);

  const data = [
    {
      x: sortedData.map((p) => p.x),
      y: sortedData.map((p) => p.y),
      type: "scatter",
      mode: "lines",
      name: "Experimental",
      line: {
        color: "#2563eb",
        width: 2,
        shape: "linear",
      },
      hovertemplate:
        "<b>Angle</b>: %{x:.6f}°<br>" + 
        "<b>Intensity</b>: %{y:.2f} a.u.<extra></extra>",
    },
    {
      x: peakPositions.map(Number),
      y: lockedPeakIntensities, // <-- Now physically locked to the blue line!
      type: "scatter",
      mode: "markers",
      name: "Detected Peaks",
      marker: {
        color: "#16a34a",
        size: 11, // Made slightly larger so it's clearly visible
        symbol: "triangle-up",
        line: {
          color: "#166534",
          width: 1,
        },
      },
      hovertemplate:
        "<b>Peak</b><br>" +
        "Angle: %{x:.6f}°<br>" + 
        "Intensity: %{y:.2f} a.u.<extra></extra>",
    },
  ];

  const layout = {
    title: {
      text: title,
      font: {
        size: 18,
        family: "Inter, 'JetBrains Mono', sans-serif",
        weight: "bold",
      },
    },
    xaxis: {
      title: { text: xAxisLabel, font: { size: 14, weight: "bold" } },
      showgrid: true,
      gridcolor: "#e5e7eb",
      zeroline: false,
      tickfont: { size: 12 },
    },
    yaxis: {
      title: { text: "Intensity (a.u.)", font: { size: 14, weight: "bold" } },
      showgrid: true,
      gridcolor: "#e5e7eb",
      zeroline: false,
      tickfont: { size: 12 },
    },
    hovermode: "x unified",
    legend: {
      orientation: "h",
      y: -0.22,
      font: { size: 13 },
    },
    margin: { t: 60, b: 80, l: 80, r: 30 },
    plot_bgcolor: "#ffffff",
    paper_bgcolor: "#ffffff",
    font: {
      family: "Inter, 'JetBrains Mono', sans-serif",
      color: "#111827",
    },
  };

  return (
    <Plot
      data={data}
      layout={layout}
      useResizeHandler
      style={{ width: "100%", height: "450px" }}
      config={{
        responsive: true,
        displaylogo: false,
        scrollZoom: true,
        toImageButtonOptions: {
          format: "png",
          filename: "XRD_Single_Graph",
          width: 1920,
          height: 1080,
          scale: 2,
        },
      }}
    />
  );
}