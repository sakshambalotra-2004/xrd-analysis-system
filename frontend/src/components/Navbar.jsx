// ============================================================
// components/Navbar.jsx
// ============================================================
import React, { useState } from "react";
import { Link } from "react-router-dom";
import Sidebar, { SidebarToggle } from "./Sidebar";

const s = {
  nav: {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    height: "52px",
    backgroundColor: "#1B3A6B",
    borderBottom: "1px solid #16305a",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 20px",
    zIndex: 101,
    boxShadow: "0 1px 4px rgba(0,0,0,0.15)",
    gap: "12px",
  },
  left: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  brandLink: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    textDecoration: "none",
  },
  brandIcon: {
    width: "28px",
    height: "28px",
    borderRadius: "6px",
    backgroundColor: "rgba(255,255,255,0.12)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },
  brandName: {
    fontSize: "15px",
    fontWeight: "600",
    color: "#ffffff",
    letterSpacing: "0.01em",
    fontFamily: "'Inter', sans-serif",
  },
  right: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  version: {
    fontSize: "11px",
    fontWeight: "600",
    letterSpacing: "0.08em",
    color: "rgba(255,255,255,0.4)",
    fontFamily: "'JetBrains Mono', monospace",
    textTransform: "uppercase",
  },
};

export default function Navbar() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <>
      <nav style={s.nav}>
        <div style={s.left}>
          <SidebarToggle
            open={sidebarOpen}
            onToggle={() => setSidebarOpen((v) => !v)}
          />
          <Link to="/dashboard" style={s.brandLink}>
            <div style={s.brandIcon}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                stroke="#ffffff" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3"/>
                <path d="M12 2v2m0 16v2M4.22 4.22l1.42 1.42m12.72 12.72 1.42 1.42M2 12h2m16 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
              </svg>
            </div>
            <span style={s.brandName}>XRD Analysis</span>
          </Link>
        </div>
        <div style={s.right}>
          <span style={s.version}>v1.0</span>
        </div>
      </nav>

      {/* Sidebar rendered alongside Navbar so they share open state */}
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
    </>
  );
}