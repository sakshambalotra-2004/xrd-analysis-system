import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query"; // Integrated React Query
import { toast } from "react-toastify";
import { analysisApi } from "../api/analysisApi";
import PeakTable from "../components/PeakTable";
import ConfidenceCard from "../components/ConfidenceCard";
import XRDGraph from "../components/XRDGraph";
import OverlayGraph from "../components/OverlayGraph";

// ─────────────────────────────────────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Derive the colour token for a given polytype string.
 * Returns one of: "cubic" | "hexagonal" | "rhombohedral" | "default"
 */
function polytypeToken(polytype = "") {
  const p = polytype.toLowerCase();
  if (p.includes("3c") || p.includes("cubic")) return "cubic";
  if (p.includes("6h") || p.includes("4h") || p.includes("2h") || p.includes("hexagonal")) return "hexagonal";
  if (p.includes("15r") || p.includes("3r") || p.includes("rhombohedral")) return "rhombohedral";
  return "default";
}

const TOKEN_STYLES = {
  cubic: { bg: "#eff6ff", text: "#1e40af", border: "#bfdbfe", dot: "#3b82f6" },
  hexagonal: { bg: "#f0fdf4", text: "#166534", border: "#bbf7d0", dot: "#22c55e" },
  rhombohedral: { bg: "#f5f3ff", text: "#5b21b6", border: "#ddd6fe", dot: "#8b5cf6" },
  default: { bg: "#f3f4f6", text: "#374151", border: "#e5e7eb", dot: "#9ca3af" },
};

/**
 * Build a deduplicated list of { phaseName, polytype } objects from matched_peaks.
 * This is the ground-truth source because each peak row carries its own polytype.
 * Falls back to the flat detected_phases string only if matched_peaks is empty.
 */
function derivePhaseList(matchedPeaks = [], detectedPhasesRaw = "", fallbackPolytype = "") {
  if (matchedPeaks && matchedPeaks.length > 0) {
    const seen = new Map(); // key: "phaseName||polytype"
    matchedPeaks.forEach((pk) => {
      const name = pk.phase_name || "Unknown Phase";
      const poly = pk.polytype || "";
      const key = `${name}||${poly}`;
      if (!seen.has(key)) seen.set(key, { phaseName: name, polytype: poly });
    });
    return Array.from(seen.values());
  }

  // Fallback: parse the flat string
  const names = Array.isArray(detectedPhasesRaw)
    ? detectedPhasesRaw
    : typeof detectedPhasesRaw === "string"
      ? detectedPhasesRaw.split(",").map((p) => p.trim()).filter(Boolean)
      : [];
  return names.map((name) => ({ phaseName: name, polytype: fallbackPolytype }));
}

// ─────────────────────────────────────────────────────────────────────────────
// PEAK ALIGNMENT MAP (inline — single source of truth)
// ─────────────────────────────────────────────────────────────────────────────

function PeakAlignmentMap({ peaks = [] }) {
  if (!peaks || peaks.length === 0) {
    return (
      <p style={{ color: "#6b7280", fontStyle: "italic" }}>
        No phase alignments available.
      </p>
    );
  }

  // Group by "phase_name (polytype)" so different polytypes of the same compound
  // get separate cards rather than being merged under one vague heading.
  const groupedByPolytype = peaks.reduce((groups, peak) => {
    const poly = peak.polytype || "";
    const name = peak.phase_name || "Unknown Phase";
    const label = poly ? `${name}  —  ${poly}` : name;
    if (!groups[label]) groups[label] = { polytype: poly, phaseName: name, peaks: [] };
    groups[label].peaks.push(peak);
    return groups;
  }, {});

  return (
    <div style={{ fontFamily: "Inter, sans-serif", marginTop: "20px" }}>
      {Object.entries(groupedByPolytype).map(([label, group]) => {
        const token = polytypeToken(group.polytype);
        const colors = TOKEN_STYLES[token];

        return (
          <div
            key={label}
            style={{
              marginBottom: "25px",
              border: `1px solid ${colors.border}`,
              borderRadius: "8px",
              backgroundColor: "#ffffff",
              boxShadow: "0 1px 3px 0 rgba(0,0,0,0.05)"
            }}
          >
            {/* ── Section header ─────────────────────────────────────── */}
            <div
              style={{
                padding: "12px 16px",
                backgroundColor: colors.bg,
                borderBottom: `1px solid ${colors.border}`,
                borderTopLeftRadius: "7px",
                borderTopRightRadius: "7px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center"
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                {/* Coloured dot acts as a quick visual identifier */}
                <div style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: colors.dot, flexShrink: 0 }} />
                <div>
                  <h4 style={{ margin: 0, color: "#111827", fontSize: "15px", fontWeight: "700" }}>
                    {group.phaseName}
                  </h4>
                  {group.polytype && (
                    <span
                      style={{
                        display: "inline-block",
                        marginTop: "2px",
                        fontSize: "12px",
                        fontWeight: "700",
                        color: colors.text,
                        backgroundColor: "#ffffff",
                        border: `1px solid ${colors.border}`,
                        padding: "1px 8px",
                        borderRadius: "12px"
                      }}
                    >
                      {group.polytype}
                    </span>
                  )}
                </div>
              </div>
              <span
                style={{
                  fontSize: "12px",
                  backgroundColor: "#ffffff",
                  padding: "2px 10px",
                  borderRadius: "20px",
                  fontWeight: "600",
                  border: "1px solid #d1d5db",
                  color: "#374151"
                }}
              >
                {group.peaks.length} Reflections Aligned
              </span>
            </div>

            {/* ── Side-by-side mapping rows ───────────────────────────── */}
            <div style={{ padding: "16px" }}>
              {/* Column headers */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr auto 1fr",
                  gap: "12px",
                  fontWeight: "600",
                  fontSize: "12px",
                  color: "#6b7280",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  marginBottom: "8px",
                  paddingBottom: "6px",
                  borderBottom: "1px solid #f3f4f6"
                }}
              >
                <div>Experimental Input Data</div>
                <div style={{ textAlign: "center" }}>Δ / Match</div>
                <div>Standard Card Reference</div>
              </div>

              {group.peaks.map((peak, idx) => {
                const exp2Theta = Number(peak.two_theta_exp || 0).toFixed(6); // Changed to 6 decimals
                const std2Theta = Number(peak.two_theta_std || 0).toFixed(6); // Changed to 6 decimals
                const delta = Number(peak.delta_two_theta || 0);
                const sign = delta > 0 ? "+" : "";
                const tight = Math.abs(delta) <= 0.04;

                return (
                  <div
                    key={idx}
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr auto 1fr",
                      gap: "12px",
                      alignItems: "center",
                      padding: "10px 0",
                      borderBottom:
                        idx === group.peaks.length - 1 ? "none" : "1px solid #f9fafb"
                    }}
                  >
                    {/* Left: Experimental */}
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <div
                        style={{
                          width: "8px",
                          height: "8px",
                          borderRadius: "50%",
                          backgroundColor: "#ef4444",
                          flexShrink: 0
                        }}
                      />
                      <div>
                        <span style={{ fontWeight: "700", color: "#111827", fontSize: "14px" }}>
                          {exp2Theta}°
                        </span>{" "}
                        2θ
                        <div style={{ fontSize: "12px", color: "#6b7280" }}>
                          Observed Bragg Reflection
                        </div>
                      </div>
                    </div>

                    {/* Centre: Delta badge + arrow */}
                    <div style={{ textAlign: "center", minWidth: "96px" }}>
                      <div
                        style={{
                          fontSize: "11px",
                          fontWeight: "700",
                          color: tight ? "#16a34a" : "#dc2626",
                          backgroundColor: tight ? "#dcfce7" : "#fee2e2",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          display: "inline-block"
                        }}
                      >
                        Δ2θ: {sign}{delta.toFixed(6)}° {/* Changed to 6 decimals */}
                      </div>
                      <div style={{ color: "#d1d5db", fontSize: "13px", marginTop: "2px" }}>
                        ──────►
                      </div>
                    </div>

                    {/* Right: Standard card */}
                    <div
                      style={{
                        display: "flex",
                        alignItems: "flex-start",
                        gap: "8px",
                        justifyContent: "space-between"
                      }}
                    >
                      <div>
                        <span
                          style={{
                            fontWeight: "700",
                            color: colors.text,
                            fontSize: "14px"
                          }}
                        >
                          {std2Theta}°
                        </span>{" "}
                        2θ
                        <div style={{ fontSize: "12px", color: "#4b5563" }}>
                          ({peak.h} {peak.k} {peak.l}) Miller Plane
                        </div>
                      </div>
                      <div
                        style={{
                          fontSize: "11px",
                          color: "#9ca3af",
                          fontStyle: "italic",
                          textAlign: "right",
                          maxWidth: "90px"
                        }}
                      >
                        {peak.phase_name}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// RESULTS PAGE
// ─────────────────────────────────────────────────────────────────────────────

export default function ResultsPage() {
  const { fileId } = useParams();
  const navigate = useNavigate();

  // Local UI states
  const [graphViewMode, setGraphViewMode] = useState("interactive");
  const [imageError, setImageError] = useState(false);

  // React Query handles the data fetching, caching, and loading state automatically
  const { data: result, isLoading, isError } = useQuery({
    queryKey: ["analysis", fileId],
    queryFn: async () => {
      try {
        const data = await analysisApi.getAnalysis(fileId);
        console.log("ANALYSIS RESULT:", data);
        return data;
      } catch (err) {
        console.error(err);
        toast.error("Failed to load analysis results.");
        throw err;
      }
    },
    retry: 1, // Optional: retry once before failing
  });

  if (isLoading) return <div className="page-loader">Loading results…</div>;
  if (isError || !result) return <div className="page-error">Results not found for file ID: {fileId}</div>;

  // ── Derived data ──────────────────────────────────────────────────────────
  const matchedPeaks = result.matched_peaks || [];

  /**
   * phaseList is the authoritative per-phase inventory.
   * Each entry: { phaseName: string, polytype: string }
   * Sourced from matched_peaks so polytypes are always accurate.
   */
  const phaseList = derivePhaseList(
    matchedPeaks,
    result.detected_phases,
    result.polytype || ""
  );

  const isMultiPhase = phaseList.length > 1;

  // ── Safe Y-axis ceiling ───────────────────────────────────────────────────
  // Prefer raw (unsmoothed) intensity; fall back to smoothed if raw isn't
  // available yet (e.g. older cached result before backend was redeployed).
  // Guard against empty arrays — Math.max(...[]) returns -Infinity.
  const _rawArr  = Array.isArray(result.full_intensity_raw)  && result.full_intensity_raw.length  > 0 ? result.full_intensity_raw  : null;
  const _smArr   = Array.isArray(result.full_intensity)      && result.full_intensity.length      > 0 ? result.full_intensity      : null;
  const _bestArr = _rawArr ?? _smArr ?? [0];
  const yMaxXRD     = Math.max(..._bestArr) * 1.08;
  const yMaxOverlay = Math.max(..._bestArr) * 1.15;
  console.log("[YAxis] raw_len:", _rawArr?.length, "smoothed_len:", _smArr?.length, "ceiling:", yMaxXRD);

  return (
    <div className="page results-page">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="page-header">
        <h1>Analysis Results</h1>
        <div className="header-actions" style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <button className="btn btn-secondary" onClick={() => navigate(`/analysis/${fileId}`)}>
            Detailed Analysis
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

      {/* ── Multi-phase alert banner ────────────────────────────────────────── */}
      {isMultiPhase && (
        <div
          className="card multiphase-alert-banner"
          style={{
            borderLeft: "4px solid #eab308",
            backgroundColor: "#fef9c3",
            padding: "12px 16px",
            marginBottom: "20px",
            borderRadius: "6px"
          }}
        >
          <p style={{ margin: 0, color: "#854d0e", fontWeight: "600" }}>
            ⚠️ Multi-Phase Mixture Detected: This sample contains{" "}
            {phaseList.length} distinct crystalline phases or polytypes.
          </p>
        </div>
      )}

      {/* ── Summary metrics grid ────────────────────────────────────────────── */}
      <div className="results-grid">
        <ConfidenceCard
          compoundName={result.compound_name}
          formula={result.formula}
          crystalSystem={result.crystal_system}
          spaceGroup={result.space_group}
          confidenceScore={result.confidence_score}
          detectedPhases={result.detected_phases}
        />

        {/* ── Identified Crystalline Phases card ─────────────────────────── */}
        <div className="card phase-distribution-card">
          <h3>Identified Crystalline Phases</h3>
          <p
            className="text-muted"
            style={{ fontSize: "14px", marginBottom: "16px" }}
          >
            The following phase–polytype pairs were resolved from the Bragg
            reflection matching loop:
          </p>

          <div
            className="phase-badges-container"
            style={{ display: "flex", flexDirection: "column", gap: "10px" }}
          >
            {phaseList.length === 0 ? (
              <div
                style={{
                  padding: "14px",
                  backgroundColor: "#f9fafb",
                  borderRadius: "6px",
                  color: "#6b7280",
                  fontSize: "14px",
                  fontStyle: "italic",
                  border: "1px dashed #d1d5db"
                }}
              >
                No crystalline phases identified — amorphous or disordered matrix.
              </div>
            ) : (
              phaseList.map(({ phaseName, polytype }, idx) => {
                const token = polytypeToken(polytype);
                const colors = TOKEN_STYLES[token];

                // Count reflections belonging to this specific phase+polytype
                const reflectionCount = matchedPeaks.filter(
                  (pk) =>
                    (pk.phase_name || "") === phaseName &&
                    (pk.polytype || "") === polytype
                ).length;

                return (
                  <div
                    key={`${phaseName}||${polytype}||${idx}`}
                    className="phase-badge-item"
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "12px 14px",
                      borderRadius: "6px",
                      backgroundColor: colors.bg,
                      border: `1px solid ${colors.border}`
                    }}
                  >
                    {/* Left: name + polytype chip */}
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <div
                        style={{
                          width: "10px",
                          height: "10px",
                          borderRadius: "50%",
                          backgroundColor: colors.dot,
                          flexShrink: 0
                        }}
                      />
                      <div>
                        <span style={{ fontWeight: "700", color: colors.text, fontSize: "14px" }}>
                          {phaseName}
                        </span>
                        {polytype && (
                          <span
                            style={{
                              marginLeft: "8px",
                              fontSize: "12px",
                              padding: "2px 8px",
                              borderRadius: "4px",
                              backgroundColor: "#ffffff",
                              color: colors.text,
                              fontWeight: "700",
                              border: `1px solid ${colors.border}`
                            }}
                          >
                            {polytype}
                          </span>
                        )}
                        {/* Primary / secondary label */}
                        <span
                          style={{
                            marginLeft: "8px",
                            fontSize: "11px",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            backgroundColor: idx === 0
                              ? TOKEN_STYLES.cubic.bg
                              : "#f3f4f6",
                            color: idx === 0
                              ? TOKEN_STYLES.cubic.text
                              : "#6b7280",
                            fontWeight: "600"
                          }}
                        >
                          {idx === 0 ? "Primary Phase" : "Secondary / Trace"}
                        </span>
                      </div>
                    </div>

                    {/* Right: reflection count */}
                    {reflectionCount > 0 && (
                      <span
                        style={{
                          fontSize: "12px",
                          color: "#6b7280",
                          backgroundColor: "#ffffff",
                          border: "1px solid #e5e7eb",
                          padding: "2px 8px",
                          borderRadius: "12px",
                          fontWeight: "600",
                          whiteSpace: "nowrap"
                        }}
                      >
                        {reflectionCount} peaks
                      </span>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* ── Experimental XRD pattern ────────────────────────────────────────── */}
<div className="card chart-card" style={{ marginTop: "20px" }}>
  <h3>Experimental XRD Pattern</h3>
  <XRDGraph
    twoTheta={result.full_two_theta}
    intensity={_bestArr}
    peakPositions={result.peaks.map((p) => p.two_theta)}
    peakIntensities={result.peaks.map((p) => p.intensity)}
    yMax={yMaxXRD}
  />
</div>

      {/* ── Overlay comparison card ─────────────────────────────────────────── */}
      <div className="card" style={{ marginTop: "20px" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "15px",
            flexWrap: "wrap",
            gap: "10px"
          }}
        >
          <h3>
            Overlay Comparison — Experimental vs Standard (
            {result.formula}
            {/* Show all detected polytypes in the heading */}
            {phaseList.some((p) => p.polytype) && (
              <span style={{ color: "#6b7280", fontWeight: "400", fontSize: "14px" }}>
                {" "}[{phaseList.filter((p) => p.polytype).map((p) => p.polytype).join(" · ")}]
              </span>
            )}
            )
          </h3>

          <div
            className="btn-group"
            style={{
              display: "inline-flex",
              backgroundColor: "#f3f4f6",
              padding: "4px",
              borderRadius: "6px"
            }}
          >
            {["interactive", "publication"].map((mode) => (
              <button
                key={mode}
                className="btn"
                style={{
                  padding: "6px 12px",
                  fontSize: "13px",
                  borderRadius: "4px",
                  border: "none",
                  cursor: "pointer",
                  backgroundColor: graphViewMode === mode ? "#ffffff" : "transparent",
                  boxShadow: graphViewMode === mode ? "0 1px 2px 0 rgba(0,0,0,0.05)" : "none",
                  fontWeight: graphViewMode === mode ? "600" : "400"
                }}
                onClick={() => {
                  setGraphViewMode(mode);
                  if (mode === "publication") setImageError(false);
                }}
              >
                {mode === "interactive" ? "🔍 Interactive Canvas" : "📷 Origin Print Preview"}
              </button>
            ))}
          </div>
        </div>

        {graphViewMode === "interactive" || imageError ? (
          <div>
            {imageError && graphViewMode === "publication" && (
              <div
                style={{
                  padding: "8px 12px",
                  backgroundColor: "#fee2e2",
                  borderLeft: "4px solid #ef4444",
                  borderRadius: "4px",
                  marginBottom: "12px",
                  fontSize: "13px",
                  color: "#991b1b"
                }}
              >
                ℹ️ Static print preview image is missing on the server disk. Displaying
                interactive canvas as fallback.
              </div>
            )}
            <OverlayGraph
              twoTheta={result.full_two_theta || []}
              intensity={_bestArr}
              matchedPeaks={matchedPeaks}
              compoundName={result.compound_name || "Standard"}
              yMax={yMaxOverlay}
            />
          </div>
        ) : (
          <div style={{ textAlign: "center", padding: "10px", backgroundColor: "#ffffff" }}>
            <img
              src={`/api/report/${fileId}/origin-image`}
              alt="Origin Publication Canvas"
              style={{
                maxWidth: "100%",
                height: "auto",
                borderRadius: "4px",
                border: "1px solid #e5e7eb"
              }}
              onError={() => {
                console.warn("Static image not ready. Initiating Plotly fallback.");
                setImageError(true);
              }}
            />
            <p
              style={{
                fontSize: "12px",
                color: "#6b7280",
                marginTop: "8px",
                fontStyle: "italic"
              }}
            >
              ⚙️ Static preview displaying actual vector formatting rules bound into the
              exported dataset asset file.
            </p>
          </div>
        )}
      </div>

      {/* ── Crystallographic Intersection Map ──────────────────────────────── */}
      <div className="card" style={{ marginTop: "20px" }}>
        <h3>Crystallographic Intersection Map</h3>
        <p
          style={{
            fontSize: "14px",
            color: "#6b7280",
            marginTop: "-4px",
            marginBottom: "12px"
          }}
        >
          Each experimental Bragg reflection is mapped to its best-match standard
          card entry, grouped by phase and polytype.
        </p>
        <PeakAlignmentMap peaks={matchedPeaks} />
      </div>

      {/* ── Peak match numerical table ──────────────────────────────────────── */}
      <div className="card" style={{ marginTop: "20px" }}>
        <h3>Peak Match Table</h3>
        <PeakTable peaks={matchedPeaks} rawPeaks={result.peaks || []} />
      </div>
    </div>
  );
}