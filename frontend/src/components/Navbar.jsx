// ============================================================
// components/Navbar.jsx
// ============================================================
import React from "react";
import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/dashboard">
          <span className="brand-icon">⚛️</span>
          <span className="brand-name">XRD Analysis</span>
        </Link>
      </div>
      <div className="navbar-right">
        <span className="nav-version">v1.0</span>
      </div>
    </nav>
  );
}