import React from "react";

/**
 * AnalysisSummary
 * ===============
 * Compact card used on the Dashboard to represent one past analysis.
 *
 * Props
 * -----
 * result   : analysis result object
 * onClick  : click handler (navigate to results page)
 */
export function AnalysisSummary({ result, onClick }) {
  return (
    <div className="card analysis-summary-card" onClick={onClick} role="button" tabIndex={0}>
      <div className="summary-header">
        <span className="summary-formula">{result.formula || "?"}</span>
        <span className="summary-score">{result.confidence_score?.toFixed(1)}%</span>
      </div>
      <div className="summary-name">{result.compound_name}</div>
      <div className="summary-meta">
        <span>{result.crystal_system}</span>
        <span className="muted">·</span>
        <span>{result.crystallite_size_nm} nm</span>
      </div>
    </div>
  );
}

export default AnalysisSummary;

/**
 * MatchResults
 * ============
 * Shows a ranked list of candidate compound matches with scores.
 *
 * Props
 * -----
 * candidates : array of { compound_name, formula, similarity_score }
 */
export function MatchResults({ candidates = [] }) {
  if (!candidates.length) {
    return <p className="muted">No match candidates available.</p>;
  }

  return (
    <div className="match-results">
      <h4>Candidate Matches</h4>
      <ol className="match-list">
        {candidates.map((c, i) => (
          <li key={i} className="match-item">
            <span className="match-rank">#{i + 1}</span>
            <span className="match-name">{c.compound_name}</span>
            <span className="match-formula">({c.formula})</span>
            <span
              className="match-score"
              style={{ color: c.similarity_score >= 80 ? "#2ca02c" : "#ff7f0e" }}
            >
              {c.similarity_score?.toFixed(1)}%
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}

/**
 * ReportDownload
 * ==============
 * Row component for the Reports page showing file info and download button.
 *
 * Props
 * -----
 * result : analysis result object with file_id, compound_name, formula, etc.
 */
export function ReportDownload({ result }) {
  return (
    <div className="card report-row">
      <div className="report-info">
        <span className="report-compound">{result.compound_name}</span>
        <span className="report-formula">({result.formula})</span>
        <span className="report-score muted">{result.confidence_score?.toFixed(1)}% confidence</span>
        <span className="report-system muted">{result.crystal_system}</span>
      </div>
      <div className="report-actions">
        <a
          className="btn btn-primary"
          href={`/api/report/${result.file_id}`}
          target="_blank"
          rel="noreferrer"
          download
        >
          Download PDF
        </a>
      </div>
    </div>
  );
}