import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import UploadPage from "./pages/UploadPage";
import ResultsPage from "./pages/ResultsPage";
import AnalysisPage from "./pages/AnalysisPage";
import ReportsPage from "./pages/ReportsPage";

/**
 * Root application component.
 *
 * Layout:
 *   ┌─────────────────────────────────────┐
 *   │              Navbar                 │
 *   ├──────────┬──────────────────────────┤
 *   │ Sidebar  │      Page content        │
 *   └──────────┴──────────────────────────┘
 */
export default function App() {
  return (
    <div className="app-shell">
      <Navbar />
      <div className="app-body">
        <Sidebar />
        <main className="page-content">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/results/:fileId" element={<ResultsPage />} />
            <Route path="/analysis/:fileId" element={<AnalysisPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            {/* Fallback */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
      <ToastContainer position="top-right" autoClose={3500} hideProgressBar={false} />
    </div>
  );
}