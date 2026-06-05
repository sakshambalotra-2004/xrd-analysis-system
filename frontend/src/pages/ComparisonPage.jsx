import React, { useState, useCallback } from "react";
import { useQuery, useQueries } from "@tanstack/react-query";
import { analysisApi } from "../api/analysisApi";
import MultiOverlayGraph from "../components/MultiOverlayGraph";

const PALETTE = ["#1a6fc4", "#c45c1a", "#1a9c62"];

// ============================================================================
// 1. ICONS
// ============================================================================
const IconXRD = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
    <path d="M3 3v18h18"/><path d="M7 16l4-7 4 4 3-6"/>
  </svg>
);

const IconCheck = ({ color }) => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="3.5">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
);

const IconClock = () => (
  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#9aabb8" strokeWidth="2.5">
    <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
  </svg>
);

const IconSpinner = ({ color = "#1a6fc4" }) => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="3" style={{ animation: "spin 0.9s linear infinite" }}>
    <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
  </svg>
);

// ============================================================================
// 2. SUB-COMPONENTS
// ============================================================================

function SkeletonRow() {
  return (
    <div style={skeletonStyles.row}>
      <div style={{ ...skeletonStyles.block, width: 16, height: 16, borderRadius: 3 }} />
      <div style={{ flex: 1 }}>
        <div style={{ ...skeletonStyles.block, width: "55%", height: 11, marginBottom: 6 }} />
        <div style={{ ...skeletonStyles.block, width: "35%", height: 9 }} />
      </div>
    </div>
  );
}

function ScanRow({ record, isSelected, isDisabled, slotIndex, onToggle }) {
  const color = isSelected ? PALETTE[slotIndex] : null;

  return (
    <button
      onClick={() => !isDisabled && onToggle(record.file_id)}
      disabled={isDisabled}
      style={{
        ...scanRowStyles.root,
        borderColor: isSelected ? color : "#e2e8ef",
        background: isSelected ? `${color}0d` : "#fafbfc",
        opacity: isDisabled ? 0.4 : 1,
        cursor: isDisabled ? "not-allowed" : "pointer",
      }}
    >
      <div style={{
        ...scanRowStyles.indicator,
        borderColor: isSelected ? color : "#ccd3dc",
        background: isSelected ? color : "transparent",
      }}>
        {isSelected && <IconCheck color="#fff" />}
      </div>

      {isSelected && (
        <div style={{ ...scanRowStyles.slotBadge, background: color }}>
          {slotIndex + 1}
        </div>
      )}

      <div style={{ flex: 1, textAlign: "left", minWidth: 0 }}>
        <div style={scanRowStyles.compound}>
          {record.compound_name}
          {record.polytype && <span style={scanRowStyles.polytype}> ({record.polytype})</span>}
        </div>
        <div style={scanRowStyles.meta}>
          <IconClock />
          {new Date(record.uploaded_at).toLocaleString("en-GB", {
            day: "2-digit", month: "short", year: "numeric",
            hour: "2-digit", minute: "2-digit",
          })}
          {record.file_id && (
            <span style={scanRowStyles.fileId}> · {record.file_id.substring(0, 8)}</span>
          )}
        </div>
      </div>
    </button>
  );
}

// ============================================================================
// 3. MAIN PAGE COMPONENT
// ============================================================================

export default function ComparisonPage() {
  const [selectedIds, setSelectedIds] = useState([]);

  // Fetch Database History
  const { data: history = [], isLoading: historyLoading } = useQuery({
    queryKey: ["analysisHistory"],
    queryFn: () => analysisApi.getRecentHistory(20),
  });

  // Fetch Mathematical Vectors for selected files
  const selectedQueries = useQueries({
    queries: selectedIds.map(fileId => ({
      queryKey: ["analysis", fileId],
      queryFn: () => analysisApi.getAnalysis(fileId),
      staleTime: Infinity,
    })),
  });

  // Map the loaded queries to Graph-ready datasets
  const datasetsToGraph = selectedQueries
    .filter(query => query.isSuccess && query.data)
    .map(query => {
      const historicalRecord = history.find(record => record.file_id === query.data.file_id);
      
      const label = historicalRecord
        ? `${historicalRecord.compound_name}${historicalRecord.polytype ? ` (${historicalRecord.polytype})` : ""}`
        : query.data.compound_name;
        
      return { 
        name: label, 
        twoTheta: query.data.full_two_theta, 
        intensity: query.data.full_intensity 
      };
    });

  // Toggle Checkbox Logic
  const handleToggleFile = useCallback((fileId) => {
    if (selectedIds.includes(fileId)) {
      setSelectedIds(prev => prev.filter(id => id !== fileId));
    } else {
      if (selectedIds.length >= 3) return; // Prevent more than 3 selections
      setSelectedIds(prev => [...prev, fileId]);
    }
  }, [selectedIds]);

  const loadingIds = selectedQueries
    .map((query, index) => query.isLoading ? selectedIds[index] : null)
    .filter(Boolean);
    
  const slotsLeft = 3 - selectedIds.length;

  return (
    <>
      <style>{`
        /* IMPORTED HEAVIER FONT WEIGHTS (800 and 900) */
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800;900&family=DM+Sans:wght@400;500;600;700;800;900&display=swap');
        @keyframes spin    { to { transform: rotate(360deg); } }
        @keyframes shimmer { to { background-position: -200% 0; } }
        @keyframes fadeIn  { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
        * { box-sizing: border-box; }
        body { margin: 0; }
        .mog-list::-webkit-scrollbar { width: 4px; }
        .mog-list::-webkit-scrollbar-track { background: transparent; }
        .mog-list::-webkit-scrollbar-thumb { background: #dde3ea; border-radius: 4px; }
      `}</style>

      <div style={pageStyles.page}>
        
        {/* Header Section */}
        <div style={pageStyles.header}>
          <div style={pageStyles.headerLeft}>
            <div style={pageStyles.iconWrap}>
              <IconXRD />
            </div>
            <div>
              <h1 style={pageStyles.title}>MULTI-SCAN OVERLAY ANALYSIS</h1>
              <p style={pageStyles.subtitle}>Overlay up to 3 diffractograms · phase identification · inter-run comparison</p>
            </div>
          </div>

          {/* Slot Pills (Top Right) */}
          <div style={pageStyles.pills}>
            {selectedIds.map((id, index) => {
              const record = history.find(h => h.file_id === id);
              const isLoading = loadingIds.includes(id);
              return (
                <div key={id} style={{ ...pageStyles.pill, borderColor: PALETTE[index] + "70", background: PALETTE[index] + "0d" }}>
                  <span style={{ color: PALETTE[index], fontWeight: 900, fontSize: 12 }}>
                    {index + 1}
                  </span>
                  <span style={pageStyles.pillName}>
                    {record?.compound_name ?? id.substring(0, 8)}
                  </span>
                  {isLoading ? (
                    <IconSpinner color={PALETTE[index]} />
                  ) : (
                    <span style={{ ...pageStyles.pillDot, background: PALETTE[index] }} />
                  )}
                </div>
              );
            })}
            
            {slotsLeft > 0 && (
              <div style={pageStyles.pillEmpty}>
                +{slotsLeft} slot{slotsLeft > 1 ? "s" : ""}
              </div>
            )}
          </div>
        </div>

        {/* Main Body Section */}
        <div style={pageStyles.body}>
          
          {/* Left Column: Database Selector */}
          <div style={pageStyles.selectorCard}>
            <div style={pageStyles.selectorHeader}>
              <span style={pageStyles.sectionLabel}>SCAN DATABASE</span>
              <span style={pageStyles.count}>{history.length} records</span>
            </div>
            
            <div className="mog-list" style={pageStyles.list}>
              {historyLoading
                ? Array.from({ length: 5 }).map((_, i) => <SkeletonRow key={i} />)
                : history.map(record => {
                    const isSelected = selectedIds.includes(record.file_id);
                    const slotIndex  = selectedIds.indexOf(record.file_id);
                    const isDisabled = !isSelected && selectedIds.length >= 3;
                    
                    return (
                      <ScanRow 
                        key={record.file_id}
                        record={record} 
                        isSelected={isSelected}
                        isDisabled={isDisabled} 
                        slotIndex={slotIndex}
                        onToggle={handleToggleFile} 
                      />
                    );
                  })}
            </div>
            
            <div style={pageStyles.selectorFooter}>
              Raw vectors · no resampling
            </div>
          </div>

          {/* Right Column: The Graph */}
          <div style={pageStyles.graphCard}>
            <MultiOverlayGraph datasets={datasetsToGraph} />
            
            {selectedQueries.some(query => query.isLoading) && (
              <div style={pageStyles.fetchRow}>
                <IconSpinner />
                <span style={{ fontSize: 11, fontWeight: 700, fontFamily: "'JetBrains Mono',monospace", color: "#1a6fc4" }}>
                  Fetching high-resolution vectors…
                </span>
              </div>
            )}
          </div>
          
        </div>
      </div>
    </>
  );
}

// ============================================================================
// 4. COMPONENT STYLES
// ============================================================================

const skeletonStyles = {
  row: {
    display: "flex", 
    alignItems: "center", 
    gap: 12,
    padding: "10px 12px", 
    borderRadius: 5,
    background: "#f8fafc", 
    border: "1px solid #edf0f4",
  },
  block: {
    borderRadius: 3,
    background: "linear-gradient(90deg, #edf0f4 25%, #f4f6f8 50%, #edf0f4 75%)",
    backgroundSize: "200% 100%",
    animation: "shimmer 1.4s infinite",
  },
};

const scanRowStyles = {
  root: {
    display: "flex", 
    alignItems: "center", 
    gap: 10,
    width: "100%", 
    padding: "9px 12px",
    borderRadius: 5, 
    border: "1px solid",
    transition: "all 0.16s ease",
    position: "relative",
  },
  indicator: {
    width: 17, 
    height: 17, 
    borderRadius: 4,
    border: "2px solid", // Bolder border
    display: "flex", 
    alignItems: "center", 
    justifyContent: "center",
    flexShrink: 0, 
    transition: "all 0.14s",
  },
  slotBadge: {
    position: "absolute", 
    top: -6, 
    left: 24,
    width: 15, 
    height: 15, 
    borderRadius: 8,
    fontSize: 9, 
    fontWeight: 900, // Bolder
    fontFamily: "'JetBrains Mono', monospace",
    color: "#fff",
    display: "flex", 
    alignItems: "center", 
    justifyContent: "center",
    boxShadow: "0 0 0 2px #fff",
  },
  compound: {
    fontSize: 13, 
    fontWeight: 800, // Bolder
    color: "#1e2d3d",
    fontFamily: "'JetBrains Mono', monospace",
    whiteSpace: "nowrap", 
    overflow: "hidden", 
    textOverflow: "ellipsis",
  },
  polytype: { 
    color: "#4a5568", 
    fontWeight: 700 // Bolder
  },
  meta: {
    display: "flex", 
    alignItems: "center", 
    gap: 5,
    marginTop: 3, 
    fontSize: 11, 
    fontWeight: 600, // Bolder
    color: "#7a8a99",
    fontFamily: "'JetBrains Mono', monospace",
  },
  fileId: { 
    color: "#b8c4ce" 
  },
};

const pageStyles = {
  page: {
    minHeight: "100vh",
    background: "#f0f2f5",
    fontFamily: "'DM Sans', sans-serif",
    color: "#1e2d3d",
    padding: "28px 32px",
    animation: "fadeIn 0.28s ease",
  },
  header: {
    display: "flex", 
    alignItems: "flex-start",
    justifyContent: "space-between", 
    flexWrap: "wrap",
    gap: 16, 
    marginBottom: 22, 
    paddingBottom: 18,
    borderBottom: "1px solid #dde3ea",
  },
  headerLeft: { 
    display: "flex", 
    alignItems: "center", 
    gap: 13 
  },
  iconWrap: {
    width: 40, 
    height: 40, 
    borderRadius: 8,
    background: "rgba(26,111,196,0.1)",
    border: "2px solid rgba(26,111,196,0.3)", // Bolder border
    color: "#1a6fc4",
    display: "flex", 
    alignItems: "center", 
    justifyContent: "center",
    flexShrink: 0,
  },
  title: {
    margin: 0, 
    fontSize: 16, 
    fontWeight: 900, // Extra Bold
    letterSpacing: "0.1em", 
    color: "#1e2d3d",
    fontFamily: "'JetBrains Mono', monospace",
  },
  subtitle: {
    margin: "3px 0 0", 
    fontSize: 11,
    fontWeight: 600, // Bolder
    color: "#6b7a8a", 
    fontFamily: "'JetBrains Mono', monospace",
    letterSpacing: "0.03em",
  },
  pills: { 
    display: "flex", 
    alignItems: "center", 
    gap: 8, 
    flexWrap: "wrap" 
  },
  pill: {
    display: "flex", 
    alignItems: "center", 
    gap: 7,
    padding: "4px 11px", 
    border: "2px solid", // Bolder border
    borderRadius: 20, 
    fontSize: 11,
    fontFamily: "'JetBrains Mono', monospace",
  },
  pillName: {
    color: "#1e2d3d",
    fontWeight: 700, // Bolder
    maxWidth: 120, 
    overflow: "hidden", 
    textOverflow: "ellipsis", 
    whiteSpace: "nowrap",
  },
  pillDot: { 
    width: 7, 
    height: 7, 
    borderRadius: "50%" 
  },
  pillEmpty: {
    padding: "4px 11px", 
    borderRadius: 20,
    fontSize: 11, 
    fontWeight: 700, // Bolder
    fontFamily: "'JetBrains Mono', monospace",
    background: "#f4f6f8", 
    border: "2px dashed #ccd3dc", // Bolder border
    color: "#7a8a99",
  },
  body: { 
    display: "flex", 
    gap: 18, 
    alignItems: "flex-start", 
    flexWrap: "wrap" 
  },
  selectorCard: {
    flex: "0 0 288px",
    background: "#fff", 
    border: "2px solid #dde3ea", // Bolder border
    borderRadius: 8, 
    display: "flex", 
    flexDirection: "column",
    overflow: "hidden", 
    alignSelf: "stretch",
  },
  selectorHeader: {
    display: "flex", 
    justifyContent: "space-between", 
    alignItems: "center",
    padding: "9px 14px", 
    borderBottom: "2px solid #dde3ea", // Bolder border
    background: "#f4f6f8",
  },
  sectionLabel: {
    fontSize: 11, 
    fontWeight: 900, // Extra Bold
    letterSpacing: "0.12em",
    color: "#1a6fc4", 
    fontFamily: "'JetBrains Mono', monospace",
  },
  count: { 
    fontSize: 11, 
    fontWeight: 700, // Bolder
    fontFamily: "'JetBrains Mono', monospace", 
    color: "#9aabb8" 
  },
  list: {
    flex: 1, 
    overflowY: "auto", 
    padding: "10px",
    display: "flex", 
    flexDirection: "column", 
    gap: 6,
    maxHeight: 520,
  },
  selectorFooter: {
    padding: "7px 14px", 
    fontSize: 11,
    fontWeight: 700, // Bolder
    fontFamily: "'JetBrains Mono', monospace",
    color: "#9aabb8", 
    borderTop: "2px solid #edf0f4", // Bolder border
    background: "#f9fafb", 
    letterSpacing: "0.04em",
  },
  graphCard: {
    flex: "1 1 600px",
    background: "#fff", 
    border: "2px solid #dde3ea", // Bolder border
    borderRadius: 8, 
    overflow: "hidden",
  },
  fetchRow: {
    display: "flex", 
    alignItems: "center", 
    gap: 8,
    padding: "8px 14px", 
    borderTop: "1px solid #edf0f4",
    background: "#f9fafb",
  },
};