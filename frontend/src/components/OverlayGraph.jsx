import React from "react";
import Plot from "react-plotly.js";

/**
 * OverlayGraph
 * =============
 * Professional overlay comparison chart for:
 *  - Experimental XRD pattern
 *  - Standard reference peaks
 *
 * Fixes:
 * -------
 * ✔ Prevents weird zig-zag graph
 * ✔ Sorts experimental peaks correctly
 * ✔ Uses vertical standard reference bars
 * ✔ Better hover labels
 * ✔ Cleaner layout
 * ✔ Responsive + publication style
 */

export default function OverlayGraph({
  experimentalPeaks = [],
  matchedPeaks = [],
  compoundName = "Standard",
}) {
  /**
   * ----------------------------------------------------------------
   * SORT EXPERIMENTAL DATA
   * ----------------------------------------------------------------
   * Your graph was messy because points were connected
   * in unsorted order.
   */

  const sortedExperimental = [...experimentalPeaks].sort(
    (a, b) => a.two_theta - b.two_theta
  );

  const expAngles = sortedExperimental.map((p) => p.two_theta);

  const expIntensities = sortedExperimental.map((p) => p.intensity);

  /**
   * ----------------------------------------------------------------
   * SCALE STANDARD INTENSITIES
   * ----------------------------------------------------------------
   */

  const maxExp = Math.max(...expIntensities, 1);

  const maxStd = Math.max(
    ...matchedPeaks.map((p) => p.intensity_std || 1),
    1
  );

  const scaleFactor = maxExp / maxStd;

  /**
   * ----------------------------------------------------------------
   * STANDARD REFERENCE VERTICAL BARS
   * ----------------------------------------------------------------
   */

  const standardShapes = matchedPeaks.map((p) => ({
    type: "line",

    x0: p.two_theta_std,
    x1: p.two_theta_std,

    y0: 0,
    y1: p.intensity_std * scaleFactor,

    line: {
      color: "#ef4444",
      width: 2,
    },
  }));

  /**
   * ----------------------------------------------------------------
   * PLOT DATA
   * ----------------------------------------------------------------
   */

  const data = [
    /**
     * Experimental XRD Pattern
     */
    {
      x: expAngles,

      y: expIntensities,

      type: "scatter",

      mode: "lines",

      name: "Experimental",

      line: {
        color: "#2563eb",
        width: 3,
      },

      hovertemplate:
        "<b>Experimental Peak</b><br>" +
        "2θ: %{x:.2f}°<br>" +
        "Intensity: %{y:.2f}<extra></extra>",
    },

    /**
     * Standard Reference Markers
     */
    {
      x: matchedPeaks.map((p) => p.two_theta_std),

      y: matchedPeaks.map(
        (p) => p.intensity_std * scaleFactor
      ),

      type: "scatter",

      mode: "markers",

      name: `Standard (${compoundName})`,

      marker: {
        color: "#ef4444",
        size: 9,
        symbol: "diamond",
      },

      hovertemplate:
        "<b>Standard Peak</b><br>" +
        "2θ Std: %{x:.2f}°<br>" +
        "Scaled Intensity: %{y:.2f}<extra></extra>",
    },
  ];

  /**
   * ----------------------------------------------------------------
   * LAYOUT
   * ----------------------------------------------------------------
   */

  const layout = {
    title: {
      text: `Overlay Comparison — Experimental vs ${compoundName}`,
      font: {
        size: 22,
      },
    },

    xaxis: {
      title: {
        text: "2θ (degrees)",
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
      },

      showgrid: true,

      gridcolor: "#e5e7eb",

      zeroline: false,

      tickfont: {
        size: 13,
      },
    },

    hovermode: "closest",

    shapes: standardShapes,

    legend: {
      orientation: "h",

      x: 0,

      y: -0.18,

      font: {
        size: 13,
      },
    },

    margin: {
      t: 70,
      l: 80,
      r: 40,
      b: 80,
    },

    plot_bgcolor: "#ffffff",

    paper_bgcolor: "#ffffff",

    font: {
      family: "Inter, sans-serif",
    },
  };

  /**
   * ----------------------------------------------------------------
   * RENDER
   * ----------------------------------------------------------------
   */

  return (
    <Plot
      data={data}
      layout={layout}
      useResizeHandler
      style={{
        width: "100%",
        height: "550px",
      }}
      config={{
        responsive: true,
        displaylogo: false,
      }}
    />
  );
}