import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import { analysisApi } from "../api/analysisApi";
import MatchResults from "../components/MatchResults";
import PeakTable from "../components/PeakTable";
import ConfidenceCard from "../components/ConfidenceCard";
import XRDGraph from "../components/XRDGraph";
import OverlayGraph from "../components/OverlayGraph";

/**
 * Results Page
 * ============
 * Displays the full analysis output for a given file_id:
 *  - Confidence card with compound identification
 *  - Experimental XRD pattern chart
 *  - Overlay comparison chart
 *  - Peak match table
 *  - Link to detailed Analysis page and PDF download
 */
export default function ResultsPage() {
  const { fileId } = useParams();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
  const load = async () => {
    try {
      const data = await analysisApi.runAnalysis(fileId);

      console.log("ANALYSIS RESULT:", data);

      setResult(data);
    } catch (err) {
      console.error(err);
      toast.error("Failed to load analysis results.");
    } finally {
      setLoading(false);
    }
  };

  load();
}, [fileId]);

  if (loading) return <div className="page-loader">Loading results…</div>;
  if (!result) return <div className="page-error">Results not found for file ID: {fileId}</div>;

  return (
    <div className="page results-page">
      <div className="page-header">
        <h1>Analysis Results</h1>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={() => navigate(`/analysis/${fileId}`)}>
            Detailed Analysis
          </button>
          <a
            className="btn btn-primary"
            href={`/api/report/${fileId}`}
            target="_blank"
            rel="noreferrer"
          >
            Download PDF Report
          </a>
        </div>
      </div>

      {/* Best match summary */}
      <div className="results-grid">
        <ConfidenceCard
          compoundName={result.compound_name}
          formula={result.formula}
          crystalSystem={result.crystal_system}
          spaceGroup={result.space_group}
          confidenceScore={result.confidence_score}
          detectedPhases={result.detected_phases}
        />

        {/* Experimental pattern */}
        <div className="card chart-card">
          <h3>Experimental XRD Pattern</h3>
          <XRDGraph
            fileId={fileId}
            twoTheta={result.peaks.map((p) => p.two_theta)}
            intensity={result.peaks.map((p) => p.intensity)}
            peakPositions={result.peaks.map((p) => p.two_theta)}
          />
        </div>
      </div>

      {/* Overlay chart */}
      <div className="card">
        <h3>Overlay Comparison — Experimental vs Standard ({result.formula})</h3>
        <OverlayGraph
          fileId={fileId}
          experimentalPeaks={result.peaks}
          matchedPeaks={result.matched_peaks}
          compoundName={result.compound_name}
        />
      </div>

      {/* Peak match table */}
      <div className="card">
        <h3>Peak Match Table</h3>
        <PeakTable peaks={result.matched_peaks} />
      </div>
    </div>
  );
}