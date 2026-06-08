import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

import Navbar from "./components/Navbar";
import ComparisonPage from "./pages/ComparisonPage";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import UploadPage from "./pages/UploadPage";
import ResultsPage from "./pages/ResultsPage";
import AnalysisPage from "./pages/AnalysisPage";
import ReportsPage from "./pages/ReportsPage";
import LoginPage from "./pages/LoginPage";
import ProtectedRoute from "./components/ProtectedRoute";

/**
 * Root application component.
 *
 * Layout:
 *   ┌─────────────────────────────────────┐
 *   │              Navbar                 │
 *   ├──────────┬──────────────────────────┤
 *   │ Sidebar  │      Page content        │
 *   └──────────┴──────────────────────────┘
 *
 *  /login is public. All other routes are protected — unauthenticated
 *  visitors are redirected to /login automatically.
 */
export default function App() {
  const isAuthed = sessionStorage.getItem("xrd_authed") === "true";

  return (
    <>
      <Routes>
        {/* ── Public ──────────────────────────────────────────────── */}
        <Route path="/login" element={
          isAuthed ? <Navigate to="/dashboard" replace /> : <LoginPage />
        } />

        {/* ── Protected (Navbar + Sidebar shell) ──────────────────── */}
        <Route path="*" element={
          <ProtectedRoute>
            <div className="app-shell">
              <Navbar />
              <div className="app-body">
                <Sidebar />
                <main className="page-content">
                  <Routes>
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/upload" element={<UploadPage />} />
                    <Route path="/compare" element={<ComparisonPage />} />
                    <Route path="/results/:fileId" element={<ResultsPage />} />
                    <Route path="/analysis/:fileId" element={<AnalysisPage />} />
                    <Route path="/reports" element={<ReportsPage />} />
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                  </Routes>
                </main>
              </div>
            </div>
          </ProtectedRoute>
        } />
      </Routes>

      <ToastContainer position="top-right" autoClose={3500} hideProgressBar={false} />
    </>
  );
}