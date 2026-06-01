/**
 * charts/StandardChart.jsx
 * ========================
 * Stem plot of reference compound peaks.
 */
import React from "react";
import Plot from "react-plotly.js";

export function StandardChart({ peaks = [], compoundName = "Standard" }) {
  const angles = peaks.map((p) => p.two_theta_std ?? p.two_theta);
  const intensities = peaks.map((p) => p.intensity_std ?? p.intensity);

  // Build vertical lines as shapes
  const shapes = angles.map((a, i) => ({
    type: "line",
    x0: a, x1: a, y0: 0, y1: intensities[i],
    line: { color: "#d62728", width: 2 },
  }));

  return (
    <Plot
      data={[
        {
          x: angles, y: intensities,
          type: "scatter", mode: "markers",
          name: compoundName,
          marker: { color: "#d62728", size: 7 },
          hovertemplate: "2θ: %{x:.3f}°<br>I: %{y:.1f}<extra></extra>",
        },
      ]}
      layout={{
        title: { text: `Standard Pattern — ${compoundName}`, font: { size: 13 } },
        xaxis: { title: "2θ (degrees)" },
        yaxis: { title: "Intensity (a.u.)", rangemode: "tozero" },
        shapes,
        margin: { t: 36, b: 52, l: 56, r: 16 },
        plot_bgcolor: "#fff", paper_bgcolor: "#fff",
      }}
      useResizeHandler
      style={{ width: "100%", height: "300px" }}
      config={{ responsive: true }}
    />
  );
}

/**
 * charts/OverlayChart.jsx
 * =======================
 * Experimental line + standard vertical markers overlaid.
 */
export function OverlayChart({ experimentalData = [], matchedPeaks = [], compoundName = "" }) {
  const maxExp = Math.max(...experimentalData.map((d) => d.intensity), 1);
  const maxStd = Math.max(...matchedPeaks.map((p) => p.intensity_std), 1);
  const scale = maxExp / maxStd;

  const shapes = matchedPeaks.map((p) => ({
    type: "line",
    x0: p.two_theta_std, x1: p.two_theta_std,
    y0: 0, y1: p.intensity_std * scale,
    line: { color: "#d62728", width: 2 },
  }));

  return (
    <Plot
      data={[
        {
          x: experimentalData.map((d) => d.two_theta),
          y: experimentalData.map((d) => d.intensity),
          type: "scatter", mode: "lines",
          name: "Experimental",
          line: { color: "#1f77b4", width: 1.5 },
        },
        {
          x: matchedPeaks.map((p) => p.two_theta_std),
          y: matchedPeaks.map((p) => p.intensity_std * scale),
          type: "scatter", mode: "markers",
          name: `Standard (${compoundName})`,
          marker: { color: "#d62728", size: 6 },
        },
      ]}
      layout={{
        title: { text: `Overlay — Exp vs ${compoundName}`, font: { size: 13 } },
        xaxis: { title: "2θ (degrees)" },
        yaxis: { title: "Intensity (a.u.)" },
        shapes,
        legend: { orientation: "h", y: -0.22 },
        margin: { t: 36, b: 68, l: 56, r: 16 },
        plot_bgcolor: "#fff", paper_bgcolor: "#fff",
      }}
      useResizeHandler
      style={{ width: "100%", height: "320px" }}
      config={{ responsive: true }}
    />
  );
}

/**
 * charts/PeakShiftChart.jsx
 * =========================
 * Bar chart showing Δ2θ (peak shift) for each matched peak.
 */
export function PeakShiftChart({ matchedPeaks = [] }) {
  const labels = matchedPeaks.map((p) => `${p.two_theta_std?.toFixed(2)}°`);
  const shifts = matchedPeaks.map((p) => {
    const exp = p.two_theta_exp ?? p.two_theta_std;
    return parseFloat((exp - p.two_theta_std).toFixed(4));
  });
  const colors = shifts.map((s) =>
    s > 0.05 ? "#d62728" : s < -0.05 ? "#1f77b4" : "#2ca02c"
  );

  return (
    <Plot
      data={[
        {
          x: labels, y: shifts,
          type: "bar",
          name: "Δ2θ",
          marker: { color: colors },
          hovertemplate: "%{x}<br>Δ2θ: %{y:.4f}°<extra></extra>",
        },
      ]}
      layout={{
        title: { text: "Peak Shift (Δ2θ per matched peak)", font: { size: 13 } },
        xaxis: { title: "Standard 2θ position" },
        yaxis: { title: "Δ2θ (degrees)", zeroline: true, zerolinecolor: "#888" },
        margin: { t: 36, b: 60, l: 60, r: 16 },
        plot_bgcolor: "#fff", paper_bgcolor: "#fff",
      }}
      useResizeHandler
      style={{ width: "100%", height: "280px" }}
      config={{ responsive: true }}
    />
  );
}