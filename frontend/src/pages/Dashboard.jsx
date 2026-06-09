import React, { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { analysisApi } from "../api/analysisApi";

// ─── Icons ────────────────────────────────────────────────────────────────────
const IconPlus = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
    <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
  </svg>
);
const IconScatter = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M3 3v18h18"/><path d="M7 16l4-7 4 4 3-6"/>
  </svg>
);
const IconConfidence = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
  </svg>
);
const IconPhase = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="9"/>
    <line x1="12" y1="3" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="21"/>
    <line x1="3" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="21" y2="12"/>
  </svg>
);
const IconUpload = () => (
  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#b8c8d8" strokeWidth="1.2">
    <polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/>
    <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/>
  </svg>
);
const IconArrow = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
  </svg>
);

// ─── Skeleton ─────────────────────────────────────────────────────────────────
function SkeletonCard() {
  return (
    <div style={sk.card}>
      <div style={{ display:"flex", justifyContent:"space-between", marginBottom:14 }}>
        <div style={{ ...sk.b, width:"42%", height:13 }} />
        <div style={{ ...sk.b, width:56, height:22, borderRadius:11 }} />
      </div>
      <div style={{ ...sk.b, width:"65%", height:20, marginBottom:9 }} />
      <div style={{ ...sk.b, width:"38%", height:13 }} />
    </div>
  );
}
const sk = {
  card: { background:"#fff", border:"1px solid #d4dce6", borderRadius:8, padding:"18px 20px" },
  b: {
    borderRadius:4,
    background:"linear-gradient(90deg,#e8edf2 25%,#f2f5f8 50%,#e8edf2 75%)",
    backgroundSize:"200% 100%", animation:"shimmer 1.4s infinite", display:"block",
  },
};

// ─── Stat card ────────────────────────────────────────────────────────────────
function StatCard({ label, value, Icon, accent, loading }) {
  return (
    <div style={st.card}>
      <div style={{ ...st.accentLine, background:accent }} />
      <div style={{ ...st.iconWrap, background:accent+"18", border:`1px solid ${accent}30`, color:accent }}>
        <Icon />
      </div>
      <div style={st.right}>
        {loading ? (
          <>
            <div style={{ ...sk.b, width:72, height:24, marginBottom:8 }} />
            <div style={{ ...sk.b, width:110, height:13 }} />
          </>
        ) : (
          <>
            <div style={st.value}>{value}</div>
            <div style={st.label}>{label}</div>
          </>
        )}
      </div>
    </div>
  );
}
const st = {
  card: {
    position:"relative", display:"flex", alignItems:"center", gap:16,
    padding:"20px 22px 20px 24px",
    background:"#fff", border:"1px solid #d4dce6", borderRadius:10, overflow:"hidden",
    boxShadow:"0 1px 4px rgba(0,0,0,0.05)",
  },
  accentLine: { position:"absolute", left:0, top:0, bottom:0, width:4, borderRadius:"10px 0 0 10px" },
  iconWrap: {
    width:46, height:46, borderRadius:10,
    display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0,
  },
  right: { flex:1, minWidth:0 },
  value: {
    fontSize:24, fontWeight:700, color:"#111d2b",
    fontFamily:"'JetBrains Mono',monospace",
    letterSpacing:"-0.02em", lineHeight:1.2,
    whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis",
  },
  label: {
    marginTop:5, fontSize:12, fontFamily:"'DM Sans',sans-serif",
    letterSpacing:"0.04em", color:"#5a6a7a", fontWeight:500,
    textTransform:"uppercase",
  },
};

// ─── Empty state ──────────────────────────────────────────────────────────────
function EmptyState({ onUpload }) {
  return (
    <div style={es.wrap}>
      <div style={es.iconBox}><IconUpload /></div>
      <p style={es.heading}>Database Empty</p>
      <p style={es.sub}>No diffraction scans on record. Upload a CSV file to begin phase identification.</p>
      <button onClick={onUpload} style={es.btn}>
        <IconPlus /> Upload First Scan
      </button>
    </div>
  );
}
const es = {
  wrap: {
    display:"flex", flexDirection:"column", alignItems:"center",
    padding:"56px 24px", border:"1px dashed #c4d0dc", borderRadius:10,
    background:"#f8fafb", textAlign:"center",
  },
  iconBox: {
    width:76, height:76, borderRadius:16,
    background:"#eef2f6", border:"1px solid #d4dce6",
    display:"flex", alignItems:"center", justifyContent:"center", marginBottom:20,
  },
  heading: { margin:"0 0 10px", fontSize:18, fontWeight:700, color:"#2a3a4a", fontFamily:"'DM Sans',sans-serif" },
  sub: { margin:"0 0 26px", fontSize:14, color:"#6a7a8a", maxWidth:340, lineHeight:1.7, fontFamily:"'DM Sans',sans-serif" },
  btn: {
    display:"flex", alignItems:"center", gap:8,
    padding:"10px 22px", borderRadius:8,
    background:"rgba(26,111,196,0.09)", border:"1px solid rgba(26,111,196,0.28)",
    color:"#1a6fc4", fontSize:14, fontFamily:"'DM Sans',sans-serif",
    fontWeight:600, cursor:"pointer", transition:"all 0.16s",
  },
};

// ─── Result row ───────────────────────────────────────────────────────────────
function ResultRow({ result, onClick }) {
  const conf = result.confidence_score ?? 0;
  const confColor = conf >= 85 ? "#178a55" : conf >= 60 ? "#b85010" : "#b52020";
  const confBg    = conf >= 85 ? "#edf8f2" : conf >= 60 ? "#fef3ec" : "#fdecea";
  return (
    <button className="db-row" onClick={onClick} style={rr.row}>
      <div style={rr.left}>
        <div style={rr.compound}>
          {result.filename
            ? result.filename.replace(/\.csv$/i, "")
            : result.compound_name || "Unknown"}
        </div>
        <div style={rr.meta}>
          <span style={rr.idBadge}>{result.file_id?.substring(0, 8) ?? "—"}</span>
          <span style={rr.dot}>·</span>
          {result.compound_name && (
            <>
              <span style={rr.compoundSub}>
                {result.compound_name}
                {result.polytype && !(result.compound_name).includes(`(${result.polytype})`)
                  ? ` (${result.polytype})` : ""}
              </span>
              <span style={rr.dot}>·</span>
            </>
          )}
          {new Date(result.uploaded_at).toLocaleDateString("en-GB", { day:"2-digit", month:"short", year:"numeric" })}
        </div>
      </div>
      <div style={{ ...rr.confBadge, background:confBg, color:confColor, border:`1px solid ${confColor}28` }}>
        {conf.toFixed(1)}%
      </div>
      <div className="db-arrow" style={rr.arrow}><IconArrow /></div>
    </button>
  );
}
const rr = {
  row: {
    display:"flex", alignItems:"center", gap:16,
    width:"100%", padding:"14px 18px",
    background:"#fafbfc", border:"1px solid #e4eaf0", borderRadius:8,
    cursor:"pointer", transition:"all 0.15s", textAlign:"left", color:"inherit",
  },
  left: { flex:1, minWidth:0 },
  compound: {
    fontSize:15, fontWeight:600, color:"#111d2b",
    fontFamily:"'DM Sans',sans-serif",
    whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis",
    marginBottom:4,
  },
  polytype: { color:"#6a7a8a", fontWeight:400 },
  meta: { display:"flex", alignItems:"center", gap:7, fontSize:13, color:"#8a9aaa", fontFamily:"'DM Sans',sans-serif" },
  dot: { color:"#c4d0dc" },
  compoundSub: { color:"#6a7a8a", fontWeight:500, fontSize:12 },
  idBadge: {
    background:"#edf0f4", borderRadius:4, padding:"1px 7px",
    fontSize:12, fontFamily:"'JetBrains Mono',monospace", color:"#6a7a8a",
  },
  confBadge: {
    fontSize:13, fontFamily:"'DM Sans',sans-serif", fontWeight:700,
    padding:"4px 12px", borderRadius:20, whiteSpace:"nowrap", flexShrink:0,
  },
  arrow: { color:"#c4d0dc", display:"flex", alignItems:"center", flexShrink:0, transition:"color 0.15s" },
};

// ─── Dashboard ────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const navigate = useNavigate();
  const { data: recentResults = [], isLoading } = useQuery({
    queryKey: ["analysisHistory"],
    queryFn: () => analysisApi.getRecentHistory(5),
  });

  const handleQuickUpload = () => navigate("/upload");
  const lastResult = recentResults[0];
  const lastCompoundDisplay = lastResult
    ? (lastResult.filename
        ? lastResult.filename.replace(/\.csv$/i, "")
        : lastResult.compound_name || "Unknown")
    : "—";
  const avgConfidence = useMemo(() => {
    if (!recentResults.length) return "—";
    const avg = recentResults.reduce((s, r) => s + (r.confidence_score || 0), 0) / recentResults.length;
    return `${avg.toFixed(1)}%`;
  }, [recentResults]);

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=DM+Sans:wght@400;500;600;700&display=swap');
        @keyframes shimmer { to { background-position: -200% 0; } }
        @keyframes fadeUp  { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:none; } }
        * { box-sizing: border-box; }
        .db-row:hover  { background:#f0f5fb !important; border-color:#b8cce0 !important; }
        .db-row:hover .db-arrow { color:#1a6fc4 !important; }
        .db-new:hover  { background:rgba(26,111,196,0.18) !important; }
      `}</style>

      <div style={pg.page}>
        <div style={pg.container}>
          
          {/* Header */}
          <div style={pg.header}>
            <div style={pg.headerLeft}>
              <div style={pg.iconWrap}><IconScatter /></div>
              <div>
                <h1 style={pg.title}>XRD Analysis Dashboard</h1>
                <p style={pg.subtitle}>Phase identification · Powder diffraction · Run history</p>
              </div>
            </div>
            <button className="db-new" onClick={handleQuickUpload} style={pg.newBtn} title="New Analysis">
              <IconPlus />
            </button>
          </div>

          {/* Stats */}
          <div style={pg.statsGrid}>
            <StatCard label="Total Analyses"  value={isLoading ? "—" : recentResults.length} Icon={IconScatter}    accent="#1a6fc4" loading={isLoading} />
            <StatCard label="Avg Confidence"  value={isLoading ? "—" : avgConfidence}         Icon={IconConfidence} accent="#178a55" loading={isLoading} />
            <StatCard label="Last Phase"      value={isLoading ? "—" : lastCompoundDisplay}   Icon={IconPhase}      accent="#b85010" loading={isLoading} />
          </div>

          {/* History */}
          <div style={pg.section}>
            <div style={pg.sectionHeader}>
              <span style={pg.sectionLabel}>Database History</span>
              {!isLoading && (
                <span style={pg.sectionCount}>{recentResults.length} record{recentResults.length !== 1 ? "s" : ""}</span>
              )}
            </div>
            {isLoading ? (
              <div style={pg.list}>{Array.from({length:3}).map((_,i)=><SkeletonCard key={i}/>)}</div>
            ) : recentResults.length === 0 ? (
              <div style={{padding:20}}><EmptyState onUpload={handleQuickUpload}/></div>
            ) : (
              <div style={pg.list}>
                {recentResults.map((r,i) => (
                  <div key={r.file_id} style={{animation:`fadeUp 0.22s ease both`,animationDelay:`${i*0.05}s`}}>
                    <ResultRow result={r} onClick={() => navigate(`/results/${r.file_id}`)} />
                  </div>
                ))}
              </div>
            )}
          </div>
          
        </div>
      </div>
    </>
  );
}

const pg = {
  page: {
    minHeight: "calc(100vh - 52px)", 
    padding: "32px 36px",
  },
  container: {
    maxWidth: "1100px",
    margin: "0 auto",
    width: "100%",
  },
  header: {
    display:"flex", alignItems:"center", justifyContent:"space-between",
    flexWrap:"wrap", gap:16, marginBottom:28, paddingBottom:22,
    borderBottom:"1px solid #d4dce6",
  },
  headerLeft: { display:"flex", alignItems:"center", gap:14 },
  iconWrap: {
    width:44, height:44, borderRadius:10,
    background:"rgba(26,111,196,0.1)", border:"1px solid rgba(26,111,196,0.22)",
    color:"#1a6fc4", display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0,
  },
  title: {
    margin:0, fontSize:22, fontWeight:700, color:"#111d2b",
    fontFamily:"'DM Sans',sans-serif", letterSpacing:"-0.01em",
  },
  subtitle: { margin:"4px 0 0", fontSize:13, color:"#6a7a8a", fontFamily:"'DM Sans',sans-serif" },
  newBtn: {
    width:40, height:40, borderRadius:10, display:"flex", alignItems:"center", justifyContent:"center",
    background:"rgba(26,111,196,0.1)", border:"1px solid rgba(26,111,196,0.22)",
    color:"#1a6fc4", cursor:"pointer", transition:"all 0.16s", flexShrink:0,
  },
  statsGrid: {
    display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(220px,1fr))",
    gap:16, marginBottom:24,
  },
  section: {
    background:"#fff", border:"1px solid #d4dce6",
    borderRadius:10, overflow:"hidden", boxShadow:"0 1px 4px rgba(0,0,0,0.04)",
  },
  sectionHeader: {
    display:"flex", alignItems:"center", justifyContent:"space-between",
    padding:"14px 18px", background:"#f4f7fa", borderBottom:"1px solid #d4dce6",
  },
  sectionLabel: { fontSize:14, fontWeight:700, color:"#2a3a4a", fontFamily:"'DM Sans',sans-serif" },
  sectionCount: { fontSize:13, color:"#8a9aaa", fontFamily:"'DM Sans',sans-serif" },
  list: { display:"flex", flexDirection:"column", gap:8, padding:"14px" },
};