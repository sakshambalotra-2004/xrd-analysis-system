import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import UploadBox from "../components/UploadBox";
import { uploadApi } from "../api/uploadApi";
import { analysisApi } from "../api/analysisApi";

/**
 * Upload Page
 * ===========
 * Allows users to:
 *  1. Drag-and-drop or browse to select an XRD CSV file
 *  2. Preview metadata (rows, 2θ range) after upload
 *  3. Trigger the analysis pipeline
 *  4. Navigate to ResultsPage on success
 */
export default function UploadPage() {
  const navigate = useNavigate();
  const [uploadResult, setUploadResult] = useState(null);
  const [analysing, setAnalysing] = useState(false);

  const handleFileAccepted = async (file) => {
    try {
      toast.info(`Uploading ${file.name}…`);
      const result = await uploadApi.uploadCSV(file);
      setUploadResult(result);
      toast.success(`Uploaded successfully — ${result.rows} rows detected.`);
    } catch (err) {
      toast.error(`Upload failed: ${err.message}`);
    }
  };

  const handleAnalyse = async () => {
    if (!uploadResult) return;
    setAnalysing(true);
    try {
      toast.info("Running analysis pipeline…");
      const analysis = await analysisApi.runAnalysis(uploadResult.file_id);

      // Persist to recent list
      const stored = JSON.parse(localStorage.getItem("xrd_recent") || "[]");
      stored.unshift(analysis);
      localStorage.setItem("xrd_recent", JSON.stringify(stored.slice(0, 20)));

      toast.success(`Analysis complete — ${analysis.compound_name} identified!`);
      navigate(`/results/${uploadResult.file_id}`);
    } catch (err) {
      toast.error(`Analysis failed: ${err.message}`);
    } finally {
      setAnalysing(false);
    }
  };

  return (
    <div className="page upload-page">
      <div className="page-header">
        <h1>Upload XRD Data</h1>
        <p className="subtitle">
          Upload a CSV file with columns <code>2theta (°)</code> and{" "}
          <code>Intensity</code> to begin analysis.
        </p>
      </div>

      <UploadBox onFileAccepted={handleFileAccepted} />

      {uploadResult && (
        <div className="upload-preview card">
          <h3>File Preview</h3>
          <table className="info-table">
            <tbody>
              <tr><td>Filename</td><td>{uploadResult.filename}</td></tr>
              <tr><td>Data Rows</td><td>{uploadResult.rows}</td></tr>
              <tr><td>2θ Range</td><td>{uploadResult.two_theta_min}° – {uploadResult.two_theta_max}°</td></tr>
              <tr><td>File ID</td><td><code>{uploadResult.file_id}</code></td></tr>
            </tbody>
          </table>
          <div className="upload-actions">
            <button
              className="btn btn-primary"
              onClick={handleAnalyse}
              disabled={analysing}
            >
              {analysing ? "Analysing…" : "Run Analysis"}
            </button>
          </div>
        </div>
      )}

      <div className="format-hint card">
        <h4>Expected CSV Format</h4>
        <pre>{`2theta (°), Intensity\n20.543,     40\n26.347,     100\n35.922,     10\n...`}</pre>
      </div>
    </div>
  );
}