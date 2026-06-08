import React from "react";
import { Navigate, useLocation } from "react-router-dom";

/**
 * ProtectedRoute
 * -----------------------------
 * Prevents unauthenticated access
 * to protected pages.
 */
export default function ProtectedRoute({ children }) {
  const location = useLocation();

  // Check authentication
  const isAuthenticated =
    sessionStorage.getItem("xrd_authed") === "true";

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location }}
      />
    );
  }

  // Render protected content
  return children;
}