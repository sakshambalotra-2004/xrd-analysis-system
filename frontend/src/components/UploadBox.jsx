// ============================================================
// components/UploadBox.jsx
// ============================================================
import React, { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { toast } from "react-toastify";

/**
 * Drag-and-drop file upload zone.
 *
 * Props
 * -----
 * onFilesAccepted(files) — called with an array of File objects when valid CSVs are dropped.
 */
export default function UploadBox({ onFilesAccepted }) {
  const onDrop = useCallback(
    (acceptedFiles, fileRejections) => {
      // Warn the user if they tried to drag more than 3 files
      if (fileRejections.length > 0 && fileRejections[0].errors[0].code === "too-many-files") {
        toast.warning("You can only upload a maximum of 3 files at once.");
      }

      if (acceptedFiles.length > 0) {
        onFilesAccepted(acceptedFiles); // Pass the whole array!
      }
    },
    [onFilesAccepted]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"], "text/plain": [".txt"] },
    maxFiles: 3, // THE FIX: Allow up to 3 files
  });

  return (
    <div
      {...getRootProps()}
      className={["upload-box", isDragActive ? "upload-box--active" : ""].join(" ").trim()}
      style={{ cursor: "pointer" }}
    >
      <input {...getInputProps()} />
      <div className="upload-box-inner">
        <span className="upload-icon">📂</span>
        {isDragActive ? (
          <p>Drop the files here…</p>
        ) : (
          <>
            <p style={{ fontWeight: "600", color: "#111827", marginBottom: "4px" }}>
              Drag & drop up to 3 XRD CSV files here
            </p>
            <p className="muted" style={{ fontSize: "14px", color: "#6b7280" }}>
              or click to browse
            </p>
            <button className="btn btn-secondary" type="button" style={{ marginTop: "10px" }}>
              Choose Files
            </button>
          </>
        )}
      </div>
    </div>
  );
}