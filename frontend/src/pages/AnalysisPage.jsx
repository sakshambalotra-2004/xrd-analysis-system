import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { toast } from "react-toastify";
import { analysisApi } from "../api/analysisApi";
import CrystalInfo from "../components/CrystalInfo";
import AnalysisSummary from "../components/AnalysisSummary";

/**
 * Analysis Page
 * =============
 * Detailed crystallographic analysis for a completed run:
 *  - Crystallite size (Scherrer)
 *  - d-spacing table
 *  - Peak shift chart
 *  - Strain indicator
 *  - Multi-phase breakdown
 *  - Crystal structure information
 */
export default function AnalysisPage() {
  const { fileId } = useParams();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await analysisApi.getAnalysis(fileId);
        setResult(data);
      } catch {
        toast.error("Failed to load analysis data.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [fileId]);

  if (loading) return <div className="page-loader">Loading analysis…</div>;
  if (!result) return <div className="page-error">No analysis found.</div>;

  return (
    <div className="page analysis-page">
      <div className="page-header">
        <h1>Detailed Analysis</h1>
        <span className="file-id-badge">ID: {fileId}</span>
      </div>

      <div className="analysis-grid">
        {/* Left column — Crystal info */}
        <CrystalInfo
          compoundName={result.compound_name}
          formula={result.formula}
          crystalSystem={result.crystal_system}
          spaceGroup={result.space_group}
          crystalliteSizeNm={result.crystallite_size_nm}
          meanPeakShift={result.mean_peak_shift_deg}
          strainIndicator={result.strain_indicator}
          detectedPhases={result.detected_phases}
          confidenceScore={result.confidence_score}
        />

        {/* Right column — Analysis values */}
        <div className="analysis-metrics card">
          <h3>Analysis Results</h3>
          <table className="info-table">
            <tbody>
              <tr>
                <td>Crystallite Size (Scherrer)</td>
                <td><strong>{result.crystallite_size_nm} nm</strong></td>
              </tr>
              <tr>
                <td>Mean Peak Shift (Δ2θ)</td>
                <td>{result.mean_peak_shift_deg > 0 ? "+" : ""}{result.mean_peak_shift_deg}°</td>
              </tr>
              <tr>
                <td>Strain Indicator</td>
                <td>
                  <span className={`badge badge--${result.strain_indicator.toLowerCase()}`}>
                    {result.strain_indicator}
                  </span>
                </td>
              </tr>
              <tr>
                <td>Confidence Score</td>
                <td>{result.confidence_score}%</td>
              </tr>
              <tr>
                <td>Detected Phases</td>
                <td>{result.detected_phases.join(", ") || "Single phase"}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* d-Spacing table */}
      <div className="card">
        <h3>d-Spacing Analysis (Bragg's Law)</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>2θ exp (°)</th>
              <th>2θ std (°)</th>
              <th>Δ2θ (°)</th>
              <th>d-spacing (Å)</th>
              <th>I(rel.)</th>
              <th>h</th><th>k</th><th>l</th>
            </tr>
          </thead>
          <tbody>
            {result.matched_peaks.map((p, i) => (
              <tr key={i}>
                <td>{p.two_theta_exp.toFixed(3)}</td>
                <td>{p.two_theta_std.toFixed(3)}</td>
                <td className={p.delta_two_theta > 0 ? "positive" : "negative"}>
                  {p.delta_two_theta > 0 ? "+" : ""}{p.delta_two_theta.toFixed(4)}
                </td>
                <td>{p.d_spacing.toFixed(4)}</td>
                <td>{p.intensity_std.toFixed(0)}</td>
                <td>{p.h}</td><td>{p.k}</td><td>{p.l}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}