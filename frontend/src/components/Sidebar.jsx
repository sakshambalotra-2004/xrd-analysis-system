import React from "react";
import { NavLink, useNavigate } from "react-router-dom";

/* =========================================
   Navigation Configuration
========================================= */
const NAV_ITEMS = [
  {
    path: "/dashboard",
    icon: "🏠",
    label: "Dashboard",
  },
  {
    path: "/upload",
    icon: "⬆️",
    label: "Upload CSV",
  },
  {
    path: "/compare",
    icon: "📊",
    label: "Compare",
  },
  {
    path: "/reports",
    icon: "📄",
    label: "Reports",
  },
];

/* =========================================
   Sidebar Component
========================================= */
export default function Sidebar() {
  const navigate = useNavigate();

  /* =========================================
     Logout Handler
  ========================================= */
  const handleLogout = () => {
    sessionStorage.removeItem("xrd_authed");

    // Optional:
    // localStorage.clear();
    // sessionStorage.clear();

    navigate("/login");
  };

  /* =========================================
     Active Link Styling
  ========================================= */
  const getNavLinkClass = ({ isActive }) =>
    `sidebar-link ${
      isActive ? "sidebar-link--active" : ""
    }`;

  return (
    <aside className="sidebar">
      {/* =====================================
          Main Navigation
      ====================================== */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={getNavLinkClass}
          >
            <span className="sidebar-icon">
              {item.icon}
            </span>

            <span className="sidebar-label">
              {item.label}
            </span>
          </NavLink>
        ))}
      </nav>

      {/* =====================================
          Footer Section
      ====================================== */}
      <div className="sidebar-footer">
        <button
          type="button"
          className="sidebar-link sidebar-logout"
          onClick={handleLogout}
        >
          <span className="sidebar-icon">
            🚪
          </span>

          <span className="sidebar-label">
            Logout
          </span>
        </button>
      </div>
    </aside>
  );
}