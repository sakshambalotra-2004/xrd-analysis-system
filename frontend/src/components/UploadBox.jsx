// ============================================================
// components/UploadBox.jsx
// ============================================================
import React, { useCallback } from "react";
import { useDropzone } from "react-dropzone";

/**
 * Drag-and-drop file upload zone.
 *
 * Props
 * -----
 * onFileAccepted(file) — called with the File object when a valid CSV is dropped.
 */
export default function UploadBox({ onFileAccepted }) {
  const onDrop = useCallback(
    (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        onFileAccepted(acceptedFiles[0]);
      }
    },
    [onFileAccepted]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"], "text/plain": [".txt"] },
    maxFiles: 1,
  });

  return (
    <div
      {...getRootProps()}
      className={["upload-box", isDragActive ? "upload-box--active" : ""].join(" ").trim()}
    >
      <input {...getInputProps()} />
      <div className="upload-box-inner">
        <span className="upload-icon">📂</span>
        {isDragActive ? (
          <p>Drop the CSV here…</p>
        ) : (
          <>
            <p>Drag &amp; drop an XRD CSV file here</p>
            <p className="muted">or click to browse</p>
            <button className="btn btn-secondary" type="button">
              Choose File
            </button>
          </>
        )}
      </div>
    </div>
  );
}