# XRD Compound Identification and Analysis System 🔬

A powerful, full-stack web application designed for the automated processing, phase identification, and visual comparison of X-Ray Diffraction (XRD) data. The system processes experimental CSV data, matches peaks against a standard compound database (differentiating specific polytypes), and produces detailed crystallographic reports and exports.

---

## 📑 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Analysis Capabilities](#analysis-capabilities)
- [Technology Stack](#technology-stack)
- [License](#license)

---

## 📖 Overview

This system automates the tedious process of identifying crystalline compounds from raw X-ray diffraction data. A user simply uploads a CSV file containing 2θ (two-theta) angle and intensity measurements; the backend pipeline then:

1. **Filters** noise using Savitzky-Golay signal processing.
2. **Detects** significant peaks based on dynamic prominence thresholds.
3. **Matches** peaks to a standard database, successfully differentiating between complex polytypes (e.g., SiC 6H, 15R, 3C).
4. **Calculates** critical metrics like crystallite size (Scherrer equation), strain, and peak shifts.
5. **Generates** high-resolution interactive Plotly graphs, OriginLab (`.opju`) project files, and multi-page publication-ready PDF reports.

---

## ✨ Features

- **Automated Peak Detection** — Accurately isolates significant peaks from noisy background signals.
- **Polytype-Aware Phase Identification** — Matches experimental peaks to known compound standards, specifically isolating distinct crystalline polytypes.
- **Multi-Scan Comparison Dashboard** — An interactive workspace to overlay up to 3 diffractograms simultaneously, allowing researchers to observe phase transformations and peak shifts across different runs.
- **Crystallite Size & d-Spacing** — Automatically applies the Scherrer Equation and Bragg's Law to detected peaks.
- **Comprehensive PDF Reports** — Automatically generates publication-ready PDFs containing summary cards, fully wrapped peak-match tables for *every* detected phase, and high-resolution overlay graphs.
- **OriginLab Native Export** — Bypasses standard image limits by exporting raw data and verified peaks directly into a native `.opju` Origin project for professional publication formatting.
- **Data Persistence** — Keeps a local SQLite history of all uploaded scans and completed analyses for quick retrieval and comparison.
- **AI-Powered Insights (Gemini)** — Architecture prepared for LLM integration to generate human-readable executive summaries of crystallographic findings.

---

## 🏗️ System Architecture

```text
Frontend (React 18 + Vite + Plotly.js)
         │
         ▼ (REST API)
Backend (FastAPI — Python 3.11)
         │
         ├──► Signal Processing (SciPy, NumPy, Pandas)
         ├──► Document Generation (ReportLab)
         ├──► Scientific Export (Origin Extensibility)
         ▼
Database (SQLite + JSON Compound Standards)


xrd-analysis-system/
├── backend/
│   ├── app.py                    # FastAPI application entry point
│   ├── config.py                 # Pydantic environment configuration
│   ├── routes/
│   │   ├── upload_routes.py      # CSV ingestion endpoints
│   │   └── analysis_routes.py    # Pipeline trigger, history, and deletion endpoints
│   ├── services/
│   │   ├── noise_filter.py       # Savitzky-Golay smoothing
│   │   ├── peak_detector.py      # Peak detection algorithm
│   │   ├── peak_matcher.py       # Polytype-aware database matching
│   │   ├── crystal_analyzer.py   # Crystallographic computations (Scherrer, etc.)
│   │   ├── report_generator.py   # Multi-page PDF builder (ReportLab)
│   │   ├── origin_exporter.py    # Native OriginLab (.opju) integration
│   │   └── llm_service.py        # Gemini AI insight generation
│   └── database/
│       ├── standards/            # JSON files per compound
│       └── sqlite/               # Persistent analysis history
│
├── frontend/
│   ├── vite.config.js
│   └── src/
│       ├── pages/                
│       │   ├── UploadPage.jsx    # Multi-file drag-and-drop upload
│       │   ├── ResultsPage.jsx   # Single-scan analysis dashboard
│       │   └── ComparisonPage.jsx# Multi-scan interactive overlay workspace
│       ├── components/           # UI elements (PeakTable, UploadBox, Sidebar)
│       └── api/                  # Axios HTTP client wrappers

cd backend

# Create and activate a virtual environment (Recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up your environment variables
# Create a .env file and add your Google Gemini API Key:
# GEMINI_API_KEY="your_api_key_here"

# Start the FastAPI server with hot-reloading
python -m uvicorn app:app --reload

cd frontend

# Install Node modules
npm install

# Start the Vite development server
npm run dev