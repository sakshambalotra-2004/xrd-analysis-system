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
 * 1. Drag-and-drop or browse to select up to 3 XRD CSV files
 * 2. Preview metadata (rows, 2θ range) for all files after upload
 * 3. Trigger the analysis pipeline for all files sequentially
 * 4. Navigate to ResultsPage (single) or ComparisonPage (multiple)
 */
export default function UploadPage() {
  const navigate = useNavigate();
  const [uploadResults, setUploadResults] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // 1. Handle Multiple File Uploads
  const handleFilesAccepted = async (files) => {
    try {
      const results = [];
      // Loop through and upload each file to get its file_id and metadata
      for (const file of files) {
        toast.info(`Uploading ${file.name}…`, { autoClose: 2000 });
        const result = await uploadApi.uploadCSV(file);
        results.push(result);
      }
      
      setUploadResults(results);
      toast.success(`Successfully uploaded ${results.length} file(s). Ready for analysis!`);
    } catch (err) {
      console.error(err);
      toast.error(`Upload failed: ${err.message || "Please check the console."}`);
    }
  };

  // 2. Run Analysis Pipeline & Redirect
  const handleProcess = async () => {
    if (uploadResults.length === 0) return;
    setIsProcessing(true);

    try {
      toast.info(`Running analysis pipeline on ${uploadResults.length} file(s)…`);
      
      // Loop through and run the heavy math pipeline on each uploaded file
      for (const res of uploadResults) {
        await analysisApi.runAnalysis(res.file_id);
      }

      toast.success("Analysis complete!");

      // Smart Redirect based on file count
      if (uploadResults.length === 1) {
        navigate(`/results/${uploadResults[0].file_id}`);
      } else {
        navigate(`/compare`);
      }

    } catch (err) {
      console.error(err);
      toast.error(`Analysis failed: ${err.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="page upload-page">
      <div className="page-header">
        <h1>Upload XRD Data</h1>
        <p className="subtitle">
          Upload up to 3 CSV files to begin analysis or comparison.
        </p>
      </div>

      {/* Note the prop change: onFilesAccepted (plural) */}
      <UploadBox onFilesAccepted={handleFilesAccepted} />

      {uploadResults.length > 0 && (
        <div className="upload-preview card" style={{ marginTop: "20px" }}>
          <h3>File Preview</h3>
          
          <div style={{ display: "flex", flexDirection: "column", gap: "15px", marginTop: "15px" }}>
            {uploadResults.map((res, idx) => (
              <div key={res.file_id} style={{ padding: "15px", backgroundColor: "#f9fafb", borderRadius: "6px", border: "1px solid #e5e7eb" }}>
                <table className="info-table" style={{ margin: 0 }}>
                  <tbody>
                    <tr><td><strong>File {idx + 1}</strong></td><td style={{ fontWeight: "600", color: "#111827" }}>{res.filename}</td></tr>
                    <tr><td>Data Rows</td><td>{res.rows}</td></tr>
                    <tr><td>2θ Range</td><td>{res.two_theta_min}° – {res.two_theta_max}°</td></tr>
                  </tbody>
                </table>
              </div>
            ))}
          </div>

          <div className="upload-actions" style={{ marginTop: "20px" }}>
            <button
              className="btn btn-primary"
              style={{ width: "100%", padding: "12px", fontSize: "16px" }}
              onClick={handleProcess}
              disabled={isProcessing}
            >
              {isProcessing 
                ? "Analyzing Data..." 
                : uploadResults.length > 1 
                  ? `Analyze & Compare ${uploadResults.length} Files` 
                  : "Run Analysis"}
            </button>
            
            <button
              className="btn btn-secondary"
              style={{ width: "100%", marginTop: "10px" }}
              onClick={() => setUploadResults([])}
              disabled={isProcessing}
            >
              Clear & Start Over
            </button>
          </div>
        </div>
      )}

      {uploadResults.length === 0 && (
        <div className="format-hint card" style={{ marginTop: "20px" }}>
          <h4>Expected CSV Format</h4>
          <pre>{`2theta (°), Intensity\n20.543,     40\n26.347,     100\n35.922,     10\n...`}</pre>
        </div>
      )}
    </div>
  );
}