import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import { analysisApi } from "../api/analysisApi";
import CrystalInfo from "../components/CrystalInfo";

/**
 * Analysis Page
 * =============
 * Detailed crystallographic analysis for a completed run:
 * - Crystallite size (Scherrer)
 * - d-spacing table
 * - Peak shift chart
 * - Strain indicator
 * - Multi-phase breakdown
 * - Crystal structure information
 */
export default function AnalysisPage() {
  const { fileId } = useParams();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await analysisApi.getAnalysis(fileId);
        setResult(data);
      } catch (err) {
        console.error(err);
        toast.error("Failed to load analysis data.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [fileId]);

  if (loading) return <div className="page-loader">Loading analysis…</div>;
  if (!result) return <div className="page-error">No analysis found.</div>;

  // Safely parse detected phases into an array for rendering
  const phasesArray = Array.isArray(result.detected_phases)
    ? result.detected_phases
    : typeof result.detected_phases === "string"
      ? result.detected_phases.split(",").map((p) => p.trim())
      : [];

  const strainStr = result.strain_indicator || "None";

  return (
    <div className="page analysis-page">
      <div className="page-header">
        <div>
          <h1>Detailed Analysis</h1>
          <span className="file-id-badge">ID: {fileId}</span>
        </div>
        
        {/* Navigation Actions Row */}
        <div className="header-actions" style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <button className="btn btn-secondary" onClick={() => navigate(`/results/${fileId}`)}>
            ← Back to Summary Results
          </button>
          
          {result.origin_project && (
            <a
              className="btn btn-secondary"
              href={`/api/report/${fileId}/origin`}
              style={{ backgroundColor: "#10b981", color: "white" }}
              target="_blank"
              rel="noreferrer"
            >
              📊 Open in Origin (.opju)
            </a>
          )}
        </div>
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
          strainIndicator={strainStr}
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
                  <span className={`badge badge--${strainStr.toLowerCase()}`}>
                    {strainStr}
                  </span>
                </td>
              </tr>
              <tr>
                <td>Confidence Score</td>
                <td>{result.confidence_score}%</td>
              </tr>
              <tr>
                <td>Detected Phases</td>
                <td>
                  {phasesArray.length > 0 ? (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "4px" }}>
                      {phasesArray.map((phase, idx) => (
                        <span 
                          key={`${phase}-${idx}`} 
                          style={{
                            fontSize: "12px",
                            fontWeight: "600",
                            padding: "3px 8px",
                            borderRadius: "4px",
                            backgroundColor: idx === 0 ? "#e0f2fe" : "#dcfce7",
                            color: idx === 0 ? "#0369a1" : "#15803d",
                            border: idx === 0 ? "1px solid #bae6fd" : "1px solid #bbf7d0"
                          }}
                        >
                          {phase}
                        </span>
                      ))}
                    </div>
                  ) : (
                    "Single phase"
                  )}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* d-Spacing table */}
      <div className="card" style={{ marginTop: "20px" }}>
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
            {result.matched_peaks && result.matched_peaks.map((p, i) => (
              <tr key={`matched-peak-${i}`}>
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