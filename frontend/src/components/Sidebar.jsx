import React from "react";
import { NavLink } from "react-router-dom";

// Added the Compare route to the navigation array
const NAV_ITEMS = [
  { to: "/dashboard", icon: "🏠", label: "Dashboard" },
  { to: "/upload",    icon: "⬆️", label: "Upload CSV" },
  { to: "/compare",   icon: "📊", label: "Compare" },
  { to: "/reports",   icon: "📄", label: "Reports" },
];

/**
 * Sidebar
 * =======
 * Left-hand navigation sidebar. Uses NavLink for active-state highlighting.
 */
export default function Sidebar() {
  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        {NAV_ITEMS.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              ["sidebar-link", isActive ? "sidebar-link--active" : ""].join(" ").trim()
            }
          >
            <span className="sidebar-icon">{icon}</span>
            <span className="sidebar-label">{label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}