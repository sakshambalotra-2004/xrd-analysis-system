import React, { useMemo } from "react";
import Plot from "react-plotly.js";

export default function XRDGraph({
  twoTheta = [],
  intensity = [],
  peakPositions = [],
  title = "Experimental XRD Pattern",
}) {
  const peakIntensities = useMemo(
    () =>
      peakPositions.map((pos) => {
        const idx = twoTheta.reduce(
          (best, t, i) =>
            Math.abs(t - pos) < Math.abs(twoTheta[best] - pos)
              ? i
              : best,
          0
        );

        return intensity[idx] || 0;
      }),
    [twoTheta, intensity, peakPositions]
  );

  const sortedData = [...twoTheta]
  .map((x, i) => ({
    x,
    y: intensity[i],
  }))
  .sort((a, b) => a.x - b.x);

const sortedX = sortedData.map((p) => p.x);
const sortedY = sortedData.map((p) => p.y);

const data = [
  {
    x: sortedX,
    y: sortedY,
    type: "scatter",
    mode: "lines",
    name: "Experimental",
    line: {
      color: "#2563eb",
      width: 2,
      shape: "linear",
    },
    hovertemplate:
      "<b>2θ</b>: %{x:.2f}°<br>" +
      "<b>Intensity</b>: %{y:.2f}<extra></extra>",
  },
  {
    x: peakPositions,
    y: peakIntensities,
    type: "scatter",
    mode: "markers",
    name: "Detected Peaks",
    marker: {
      color: "#16a34a",
      size: 9,
      symbol: "triangle-up",
      line: {
        color: "#166534",
        width: 1,
      },
    },
    hovertemplate:
      "<b>Peak</b><br>" +
      "2θ: %{x:.2f}°<br>" +
      "Intensity: %{y:.2f}<extra></extra>",
  },
];

  const layout = {
    title: {
      text: title,
      font: {
        size: 20,
        family: "Inter, sans-serif",
      },
    },

    xaxis: {
      title: {
        text: "2θ (degrees)",
        font: {
          size: 16,
        },
      },

      showgrid: true,
      gridcolor: "#e5e7eb",

      zeroline: false,

      tickfont: {
        size: 13,
      },
    },

    yaxis: {
      title: {
        text: "Intensity (a.u.)",
        font: {
          size: 16,
        },
      },

      showgrid: true,
      gridcolor: "#e5e7eb",

      zeroline: false,

      tickfont: {
        size: 13,
      },
    },

    hovermode: "x unified",

    legend: {
      orientation: "h",
      y: -0.22,
      font: {
        size: 13,
      },
    },

    margin: {
      t: 70,
      b: 80,
      l: 80,
      r: 30,
    },

    plot_bgcolor: "#ffffff",
    paper_bgcolor: "#ffffff",

    font: {
      family: "Inter, sans-serif",
      color: "#111827",
    },
  };

  return (
    <Plot
      data={data}
      layout={layout}
      useResizeHandler
      style={{
        width: "100%",
        height: "500px",
      }}
      config={{
        responsive: true,
        displaylogo: false,
        scrollZoom: true,
      }}
    />
  );
}