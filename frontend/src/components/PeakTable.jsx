import React from "react";

/**
 * PeakTable
 * =========
 * Renders the matched peak table: 2θ, d(Å), Δ2θ, I(rel.), h, k, l.
 *
 * Props
 * -----
 * peaks : array of matched peak objects from the analysis API.
 */
export default function PeakTable({ peaks = [] }) {
  if (!peaks.length) {
    return <p className="muted">No matched peaks available.</p>;
  }

  return (
    <div className="table-wrapper">
      <table className="data-table peak-table">
        <thead>
          <tr>
            <th>2θ exp (°)</th>
            <th>2θ std (°)</th>
            <th>Δ2θ (°)</th>
            <th>d (Å)</th>
            <th>I(rel.)</th>
            <th>h</th>
            <th>k</th>
            <th>l</th>
            <th>Match</th>
          </tr>
        </thead>
        <tbody>
          {peaks.map((p, i) => (
            <tr key={i}>
              <td>{p.two_theta_exp?.toFixed(3)}</td>
              <td>{p.two_theta_std?.toFixed(3)}</td>
              <td className={p.delta_two_theta >= 0 ? "text-positive" : "text-negative"}>
                {p.delta_two_theta >= 0 ? "+" : ""}
                {p.delta_two_theta?.toFixed(4)}
              </td>
              <td>{p.d_spacing?.toFixed(4)}</td>
              <td>{p.intensity_std?.toFixed(0)}</td>
              <td>{p.h}</td>
              <td>{p.k}</td>
              <td>{p.l}</td>
              <td className="match-tick">✓</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}