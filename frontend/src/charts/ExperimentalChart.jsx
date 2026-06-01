/**
 * charts/ExperimentalChart.jsx
 * =============================
 * Full-featured experimental XRD pattern chart with zoom, pan, and
 * hover tooltips showing 2θ and intensity values.
 */
import React from "react";
import Plot from "react-plotly.js";

export default function ExperimentalChart({ data = [], title = "Experimental XRD Pattern" }) {
  return (
    <Plot
      data={[
        {
          x: data.map((d) => d.two_theta),
          y: data.map((d) => d.intensity),
          type: "scatter",
          mode: "lines",
          name: "Experimental",
          line: { color: "#1f77b4", width: 1.5 },
          hovertemplate: "2θ: %{x:.3f}°<br>I: %{y:.1f}<extra></extra>",
        },
      ]}
      layout={{
        title: { text: title, font: { size: 13 } },
        xaxis: { title: "2θ (degrees)" },
        yaxis: { title: "Intensity (a.u.)" },
        margin: { t: 36, b: 52, l: 56, r: 16 },
        plot_bgcolor: "#fff",
        paper_bgcolor: "#fff",
      }}
      useResizeHandler
      style={{ width: "100%", height: "300px" }}
      config={{ responsive: true, displayModeBar: true }}
    />
  );
}