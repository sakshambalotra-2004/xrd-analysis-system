import React, { useState } from "react";
import { NavLink, useNavigate, useLocation } from "react-router-dom";

const NAV_ITEMS = [
  {
    path: "/dashboard",
    label: "Dashboard",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
        <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
      </svg>
    ),
  },
  {
    path: "/upload",
    label: "Upload CSV",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
      </svg>
    ),
  },
  {
    path: "/compare",
    label: "Compare",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
      </svg>
    ),
  },
  {
    path: "/reports",
    label: "Reports",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
        <polyline points="10 9 9 9 8 9"/>
      </svg>
    ),
  },
];

const SIDEBAR_WIDTH = 210;

const s = {
  overlay: {
    position: "fixed",
    inset: 0,
    backgroundColor: "rgba(0,0,0,0.25)",
    zIndex: 99,
    backdropFilter: "blur(2px)",
    WebkitBackdropFilter: "blur(2px)",
    cursor: "pointer",
  },
  sidebar: {
    width: `${SIDEBAR_WIDTH}px`,
    height: "100vh",
    position: "fixed",
    top: 0,
    left: 0,
    zIndex: 100,
    overflowY: "auto",
    backgroundColor: "#ffffff",
    borderRight: "1px solid #e5e7eb",
    display: "flex",
    flexDirection: "column",
    fontFamily: "'Inter', sans-serif",
    userSelect: "none",
    transition: "transform 0.28s cubic-bezier(0.4, 0, 0.2, 1)",
    willChange: "transform",
  },
  identity: {
    padding: "18px 16px 14px",
    borderBottom: "1px solid #f3f4f6",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  identityLeft: { flex: 1 },
  identityLabel: {
    fontSize: "9px", fontWeight: "600", letterSpacing: "0.12em",
    textTransform: "uppercase", color: "#9ca3af", marginBottom: "4px",
  },
  identityName: {
    fontSize: "13px", fontWeight: "600", color: "#111827",
    letterSpacing: "0.01em", display: "flex", alignItems: "center", gap: "7px",
  },
  identityDot: {
    display: "inline-block", width: "6px", height: "6px",
    borderRadius: "50%", backgroundColor: "#22c55e",
    flexShrink: 0, boxShadow: "0 0 5px #22c55e88",
  },
  collapseBtn: {
    width: "26px", height: "26px", borderRadius: "6px",
    border: "1px solid #e5e7eb", background: "#f9fafb",
    display: "flex", alignItems: "center", justifyContent: "center",
    cursor: "pointer", color: "#6b7280", flexShrink: 0,
    transition: "background 0.1s, color 0.1s",
  },
  navSection: { padding: "10px 8px 0" },
  navSectionLabel: {
    fontSize: "9px", fontWeight: "600", letterSpacing: "0.12em",
    textTransform: "uppercase", color: "#d1d5db", padding: "4px 8px 6px",
  },
  navLink: {
    display: "flex", alignItems: "center", gap: "10px",
    padding: "8px 10px", borderRadius: "6px",
    fontSize: "13px", fontWeight: "600", color: "#374151",
    textDecoration: "none", marginBottom: "2px", cursor: "pointer",
    border: "none", background: "transparent", width: "100%",
    textAlign: "left", letterSpacing: "0.01em",
    transition: "background 0.1s, color 0.1s",
  },
  navLinkHover: { background: "#f9fafb", color: "#111827" },
  navLinkActive: { background: "#eff6ff", color: "#1d4ed8", fontWeight: "700" },
  activeAccent: {
    position: "absolute", left: "0", top: "50%", transform: "translateY(-50%)",
    width: "3px", height: "18px", borderRadius: "0 2px 2px 0", backgroundColor: "#2563eb",
  },
  navLinkInner: {
    position: "relative", display: "flex", alignItems: "center", gap: "10px", width: "100%",
  },
  readout: {
    margin: "12px 8px 0", padding: "10px",
    backgroundColor: "#f9fafb", borderRadius: "6px", border: "1px solid #f3f4f6",
  },
  readoutRow: { display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "4px" },
  readoutKey: {
    fontSize: "9px", fontWeight: "600", letterSpacing: "0.1em",
    textTransform: "uppercase", color: "#9ca3af",
  },
  readoutVal: {
    fontSize: "11px", fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
    color: "#2563eb", letterSpacing: "0.04em",
  },
  footer: { marginTop: "auto", padding: "10px 8px 14px", borderTop: "1px solid #f3f4f6" },
  logoutBtn: {
    display: "flex", alignItems: "center", gap: "10px", padding: "8px 10px",
    borderRadius: "6px", fontSize: "13px", color: "#9ca3af",
    background: "transparent", border: "none", cursor: "pointer",
    width: "100%", textAlign: "left", letterSpacing: "0.01em",
    transition: "background 0.1s, color 0.1s",
  },
};

function NavItem({ item }) {
  const [hovered, setHovered] = useState(false);
  const location = useLocation();
  const isActive = location.pathname.startsWith(item.path);

  return (
    <NavLink
      to={item.path}
      style={{
        ...s.navLink,
        ...(hovered && !isActive ? s.navLinkHover : {}),
        ...(isActive ? s.navLinkActive : {}),
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div style={s.navLinkInner}>
        {isActive && <span style={s.activeAccent} />}
        <span style={{ color: isActive ? "#2563eb" : "inherit", flexShrink: 0 }}>
          {item.icon}
        </span>
        <span>{item.label}</span>
      </div>
    </NavLink>
  );
}

export function SidebarToggle({ open, onToggle }) {
  const [hovered, setHovered] = useState(false);
  return (
    <button
      type="button"
      onClick={onToggle}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      aria-label={open ? "Close sidebar" : "Open sidebar"}
      style={{
        width: "34px", height: "34px", borderRadius: "8px",
        border: "1px solid rgba(255,255,255,0.18)",
        background: hovered ? "rgba(255,255,255,0.15)" : "rgba(255,255,255,0.08)",
        display: "flex", alignItems: "center", justifyContent: "center",
        cursor: "pointer", color: "#ffffff", flexShrink: 0,
        transition: "background 0.15s",
      }}
    >
      {open ? (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      ) : (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
          <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/>
          <line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
      )}
    </button>
  );
}

export default function Sidebar({ open, onClose }) {
  const navigate = useNavigate();
  const [logoutHover, setLogoutHover] = useState(false);
  const [collapseBtnHover, setCollapseBtnHover] = useState(false);

  const handleLogout = () => {
    sessionStorage.removeItem("xrd_authed");
    navigate("/login");
  };

  return (
    <>
      {open && (
        <div style={s.overlay} onClick={onClose} aria-hidden="true" />
      )}

      <aside
        style={{
          ...s.sidebar,
          transform: open ? "translateX(0)" : "translateX(-100%)",
          boxShadow: open ? "4px 0 24px rgba(0,0,0,0.10)" : "none",
        }}
        aria-hidden={!open}
      >
        <div style={s.identity}>
          <div style={s.identityLeft}>
            <div style={s.identityLabel}>SSPL · SIC Lab</div>
            <div style={s.identityName}>
              <span style={s.identityDot} />
              XRD Analysis
            </div>
          </div>
          <button
            type="button"
            style={{
              ...s.collapseBtn,
              ...(collapseBtnHover ? { background: "#f3f4f6", color: "#374151" } : {}),
            }}
            onClick={onClose}
            onMouseEnter={() => setCollapseBtnHover(true)}
            onMouseLeave={() => setCollapseBtnHover(false)}
            aria-label="Close sidebar"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div style={s.navSection}>
          <div style={s.navSectionLabel}>Navigation</div>
          {NAV_ITEMS.map((item) => (
            <NavItem key={item.path} item={item} />
          ))}
        </div>

        <div style={s.readout}>
          <div style={s.readoutRow}>
            <span style={s.readoutKey}>Source</span>
            <span style={s.readoutVal}>Cu Kα</span>
          </div>
          <div style={s.readoutRow}>
            <span style={s.readoutKey}>λ</span>
            <span style={s.readoutVal}>1.5406 Å</span>
          </div>
          <div style={{ ...s.readoutRow, marginBottom: 0 }}>
            <span style={s.readoutKey}>Instrument</span>
            <span style={{ ...s.readoutVal, fontSize: "10px" }}>XPERT-PRO</span>
          </div>
        </div>

        <div style={s.footer}>
          <button
            type="button"
            style={{
              ...s.logoutBtn,
              ...(logoutHover ? { background: "#fef2f2", color: "#ef4444" } : {}),
            }}
            onClick={handleLogout}
            onMouseEnter={() => setLogoutHover(true)}
            onMouseLeave={() => setLogoutHover(false)}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            Sign out
          </button>
        </div>
      </aside>
    </>
  );
}