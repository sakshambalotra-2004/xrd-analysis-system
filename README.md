# XRD Compound Identification and Analysis System

A full-stack web application for automated X-Ray Diffraction (XRD) compound identification, peak analysis, and report generation. The system processes experimental CSV data, matches peaks against a standard compound database, and produces detailed crystallographic analysis reports.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Analysis Capabilities](#analysis-capabilities)
- [Technology Stack](#technology-stack)
- [Configuration](#configuration)
- [Authentication](#authentication)
- [Testing](#testing)
- [Bug Fixes & Changelog](#bug-fixes--changelog)
- [Future Scope](#future-scope)
- [Applications](#applications)
- [License](#license)

---

## Overview

The XRD Compound Identification and Analysis System automates the process of identifying crystalline compounds from X-ray diffraction data. A user uploads a CSV file containing 2θ (two-theta) angle and intensity measurements; the system then:

1. Filters noise from the raw signal using an adaptive Savitzky-Golay filter
2. Detects and selects significant peaks using scan-type-aware thresholds
3. Matches peaks to a standard compound database using d-spacing and Bragg's Law
4. Computes weighted similarity scores and confidence levels
5. Retrieves crystallographic information (space group, Miller indices, polytype, etc.)
6. Generates overlay graphs and downloadable PDF reports

---

## Features

- **Automated Peak Detection** — Identifies significant peaks from noisy XRD patterns with HRXRD rocking curve support
- **Phase Identification** — Matches experimental peaks to known compound standards using iterative residual matching
- **Polytype Differentiation** — Specifically isolates and identifies exact crystalline polytypes (e.g., SiC 6H, 4H, 15R-1, 15R-2, 3C, 2H)
- **Crystallite Size Analysis** — Applies the Scherrer Equation: `D = Kλ / β cos θ`
- **d-Spacing Calculation** — Uses Bragg's Law: `nλ = 2d sin θ`
- **Peak Shift Analysis** — Detects strain, stress, doping, and thermal effects
- **Multi-Phase Detection** — Identifies multiple compounds within a single sample via residual peak matching
- **Multi-Scan Comparison** — Interactive dashboard to overlay up to 3 different XRD scans simultaneously
- **Peak Indexing** — Assigns Miller indices (h, k, l) automatically
- **Overlay Visualization** — Side-by-side comparison of experimental vs. standard patterns
- **PDF Report Generation** — Produces tables, graphs, and crystallographic summaries
- **OriginLab Integration** — Exports raw data and processed peaks natively to `.opju` project files
- **AI-Powered Summaries** — Leverages Google Gemini AI to generate professional executive summaries of analysis results
- **ML-Based Prediction** — Optional machine learning predictor for crystal system classification
- **Authenticated Access** — Login-protected system with session-based access control

---

## System Architecture

```
Frontend (React + Plotly.js + Tailwind CSS)
│
▼
API Layer (FastAPI — REST)
│
▼
Backend (Python — Processing | Matching | Analysis | Visualization)
│
▼
Database (JSON Standards | SQLite | MongoDB)
```

### Pipeline Workflow

| Step | Module | Description |
|------|--------|-------------|
| 1 | `csv_reader.py` | Ingest and validate experimental data; PANalytical XPERT-PRO header support |
| 2 | `noise_filter.py` | Adaptive Savitzky-Golay smoothing — window auto-capped to 0.15° angular span |
| 3 | `peak_detector.py` | Adaptive threshold detection; raw intensity used for thresholds, smoothed for FWHM |
| 4 | `peak_matcher.py` | Compare 2θ against standard database (tolerance ±0.2°); one-to-one peak assignment |
| 5 | `similarity_engine.py` | Weighted score: 50% peak count, 30% intensity match, 20% d-spacing Gaussian decay |
| 6 | `phase_identifier.py` | Primary + residual secondary phase identification; tolerance-based angle matching |
| 7 | `crystal_analyzer.py` | Crystallite size, peak shift, strain indicator, polytype extraction |
| 8 | `graph_generator.py` | Experimental, standard, and overlay PNG charts via Matplotlib |
| 9 | `report_generator.py` | Multi-page PDF via ReportLab with polytype-annotated tables |
| 10 | `origin_exporter.py` | OriginLab `.opju` project export |

---

## Project Structure

```
xrd-analysis-system/
│
├── backend/
│   ├── a.py
│   ├── app.py
│   ├── config.py
│   ├── requirements.txt
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── experimental_data/
│   │   │
│   │   ├── sqlite/
│   │   │   ├── db_init.py
│   │   │   ├── xrd_database.py
│   │   │   ├── xrd_database.db
│   │   │   └── __init__.py
│   │   │
│   │   └── standards/
│   │       ├── Graphite_2H_00-041-1487.json
│   │       ├── Graphite_3R_01-075-2078.json
│   │       ├── Ni2Si_00-048-1339.json
│   │       ├── NiSi2_01-086-4983.json
│   │       ├── NiSi2_cubic_04-019-2896.json
│   │       ├── NiSi_00-038-0844.json
│   │       ├── SiC-15R-1_00-022-1301.json
│   │       ├── SiC-15R-2_04-007-1589.json
│   │       ├── SiC-2H_00-029-1126.json
│   │       ├── SiC-3C_00-029-1129.json
│   │       ├── SiC-4H_00-022-1317.json
│   │       ├── SiC-6H_01-075-8314.json
│   │       ├── SiO2_00-012-0708.json
│   │       ├── SiO2_00-046-1045.json
│   │       └── __init__.py
│   │
│   ├── reports/
│   │   ├── graphs/
│   │   ├── origin_files/
│   │   └── pdf_reports/
│   │
│   ├── routes/
│   │   ├── analysis_routes.py
│   │   ├── report_routes.py
│   │   └── upload_routes.py
│   │
│   ├── services/
│   │   ├── crystal_analyzer.py
│   │   ├── csv_reader.py
│   │   ├── d_spacing_calculator.py
│   │   ├── graph_generator.py
│   │   ├── ml_predictor.py
│   │   ├── noise_filter.py
│   │   ├── origin_exporter.py
│   │   ├── peak_detector.py
│   │   ├── peak_matcher.py
│   │   ├── phase_identifier.py
│   │   ├── report_generator.py
│   │   └── similarity_engine.py
│   │
│   ├── uploads/
│   │   ├── csv/
│   │   └── temp/
│   │
│   └── utils/
│       ├── constants.py
│       ├── file_handler.py
│       ├── graph_utils.py
│       ├── math_utils.py
│       ├── peak_utils.py
│       └── validation.py
│
├── frontend/
│   │
│   ├── public/
│   │   ├── favicon.png
│   │   └── icons.svg
│   │
│   ├── src/
│   │   ├── App.css
│   │   ├── App.jsx
│   │   ├── index.css
│   │   ├── main.jsx
│   │   │
│   │   ├── api/
│   │   │   ├── analysisApi.js
│   │   │   ├── reportApi.js
│   │   │   └── uploadApi.js
│   │   │
│   │   ├── assets/
│   │   │   ├── hero.png
│   │   │   ├── react.svg
│   │   │   └── vite.svg
│   │   │
│   │   ├── charts/
│   │   │   ├── ExperimentalChart.jsx
│   │   │   └── OverlayChart.jsx
│   │   │
│   │   ├── components/
│   │   │   ├── AnalysisSummary.jsx
│   │   │   ├── ConfidenceCard.jsx
│   │   │   ├── CrystalInfo.jsx
│   │   │   ├── MatchResults.jsx
│   │   │   ├── MultiOverlayGraph.jsx
│   │   │   ├── Navbar.jsx
│   │   │   ├── OverlayGraph.jsx
│   │   │   ├── PeakAlignmentMap.jsx
│   │   │   ├── PeakTable.jsx
│   │   │   ├── ProtectedRoute.jsx
│   │   │   ├── ReportDownload.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   ├── UploadBox.jsx
│   │   │   └── XRDGraph.jsx
│   │   │
│   │   ├── pages/
│   │   │   ├── AnalysisPage.jsx
│   │   │   ├── ComparisonPage.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── LoginPage.jsx
│   │   │   ├── ReportsPage.jsx
│   │   │   ├── ResultsPage.jsx
│   │   │   └── UploadPage.jsx
│   │   │
│   │   └── styles/
│   │       └── globals.css
│   │
│   ├── package.json
│   ├── vite.config.js
│   └── README.md
│
├── tests/
│   ├── test_analysis.py
│   ├── test_csv_reader.py
│   ├── test_matcher.py
│   └── test_peak_detector.py
│
├── ecosystem.config.js
├── package-lock.json
├── start_frontend_hidden.vbs
├── README.md
└── .gitignore
```

---

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+
- Gemini API Key (optional, for AI summaries)

### Backend

```bash
# Clone the repository
git clone https://github.com/sakshambalotra-2004/xrd-analysis-system
cd xrd-analysis-system/backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd ../frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173` and the API at `http://localhost:8000`.

---

## Usage

1. Navigate to `http://localhost:5173` — you will be redirected to the **Login** page.
2. Sign in with your credentials (default: `admin` / `xrd2024`).
3. Navigate to **Upload CSV** in the sidebar.
4. Choose a CSV file with columns `2theta (°)` and `Intensity`.
5. Click **Analyze** — the system processes the file through all pipeline stages.
6. View results on the **Results** page: best match compound, confidence score, peak match table, and overlay chart.
7. To compare multiple scans, navigate to `/compare` or upload up to 3 files at once.
8. Explore detailed crystallographic data on the **Analysis** page.
9. Download the full **PDF Report** or **OriginLab (.opju)** project from the Reports page.

### Input CSV Format

```
2theta (°), Intensity
20.543,     40
26.347,     100
35.922,     10
39.081,     6
...
```

PANalytical XPERT-PRO exports with metadata header blocks are supported automatically.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload CSV file |
| GET | `/api/analysis/{file_id}` | Run full analysis pipeline |
| GET | `/api/results/{file_id}` | Retrieve analysis results (includes `full_intensity_raw`) |
| DELETE | `/api/analysis/{file_id}` | Delete an analysis record and physical files |
| GET | `/api/report/{file_id}` | Download PDF report |
| GET | `/api/compounds` | List all standard compounds |
| POST | `/api/ai/summary` | Generate Gemini AI executive summary |
| GET | `/api/health` | Health check |

Full API documentation is available at `http://localhost:8000/docs` (Swagger UI).

### Analysis Response Schema

The `/api/results/{file_id}` endpoint returns the following key fields:

```json
{
  "compound_name": "Silicon Carbide",
  "formula": "SiC",
  "polytype": "6H",
  "crystal_system": "Hexagonal",
  "space_group": "P63mc",
  "confidence_score": 90.0,
  "crystallite_size_nm": 23.4,
  "mean_peak_shift_deg": 0.0412,
  "strain_indicator": "Tensile",
  "detected_phases": ["SiC (6H)", "SiC (4H)"],
  "full_two_theta": [...],
  "full_intensity": [...],
  "full_intensity_raw": [...],
  "peaks": [...],
  "matched_peaks": [...]
}
```

> `full_intensity_raw` contains the original unsmoothed intensity values. The frontend uses this for accurate Y-axis scaling on all charts.

---

## Database Schema

### Standard Compound JSON

```json
{
  "compound_name": "Silicon Carbide",
  "formula": "SiC",
  "crystal_system": "Hexagonal",
  "space_group": "P63mc",
  "polytype": "6H",
  "peaks": [
    { "two_theta": 35.60, "d": 2.52, "intensity": 100, "h": 1, "k": 0, "l": 1 },
    { "two_theta": 41.40, "d": 2.17, "intensity": 60,  "h": 1, "k": 0, "l": 2 }
  ]
}
```

### SQLite Tables

- `experiments` — uploaded file metadata, timestamps, file paths
- `analysis_results` — matched compound, polytype, confidence score, crystallite size, peak shift
- `peaks` — detected peaks per experiment (2θ, d, intensity, hkl)
- `compounds` — cached standard compound index

---

## Analysis Capabilities

| Capability | Method |
|------------|--------|
| Phase Identification | Peak matching + weighted similarity scoring |
| Crystallite Size | Scherrer Equation `D = Kλ / β cos θ` |
| d-Spacing | Bragg's Law `nλ = 2d sin θ` |
| Peak Shift | `Δ2θ = 2θ_sample − 2θ_reference` |
| Multi-Phase Detection | Residual peak matching after primary identification |
| Crystal Structure | ML classifier (cubic, hexagonal, tetragonal, etc.) |
| Peak Indexing | Automated (h k l) assignment |
| Intensity Analysis | Relative intensity comparison and normalization |

### Peak Matching Logic

A peak is considered matched when:

```
|2θ_exp − 2θ_std| ≤ 0.2°
```

Each experimental peak is assigned to at most one standard peak (one-to-one matching). Similarity score:

```
Score = (coverage × 30) + (absolute_match_bonus × 40) + (accuracy × 30)
```

This rewards both match coverage and absolute peak count, preventing small-database compounds from being unfairly favoured.

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React, Plotly.js, Tailwind CSS |
| Backend | Python, FastAPI |
| Data Processing | Pandas, NumPy, SciPy |
| Visualization | Matplotlib, Plotly |
| Machine Learning | scikit-learn, Google Gemini AI |
| Database | JSON files, SQLite, MongoDB (optional) |
| Report Generation | ReportLab, Origin Extensibility |

---

## Configuration

All configurable parameters live in `backend/config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `WAVELENGTH_ANGSTROM` | `1.5406` | Cu Kα X-ray wavelength (Å) |
| `SCHERRER_K` | `0.9` | Scherrer shape factor |
| `PEAK_MATCH_TOLERANCE_DEG` | `0.2` | Peak matching angular tolerance (°) |
| `NOISE_FILTER_WINDOW` | `21` | Savitzky-Golay window (auto-capped by adaptive logic) |
| `NOISE_FILTER_POLYORDER` | `3` | Savitzky-Golay polynomial order |
| `PEAK_HEIGHT_THRESHOLD` | `0.05` | Minimum peak height as fraction of global max |
| `PEAK_PROMINENCE_FRACTION` | `0.05` | Minimum peak prominence as fraction of global max |
| `MIN_SIMILARITY_SCORE` | `30.0` | Minimum score for a compound to be reported |

Copy `.env.example` to `.env` and adjust API keys and database paths as needed.

---

## Authentication

The system uses a simple session-based login with a single hardcoded user. Authentication state is stored in `sessionStorage` — the session clears when the browser tab is closed.

**Default credentials:**

```
Username: admin
Password: xrd2024
```

To change credentials, edit the constant at the top of `frontend/src/pages/LoginPage.jsx`:

```js
const HARDCODED_USER = { username: "admin", password: "xrd2024" };
```

All routes except `/login` are protected by `ProtectedRoute.jsx`. Unauthenticated visitors are automatically redirected to `/login`.

---

## Testing

```bash
cd backend
pytest tests/ -v
```

Test modules cover CSV ingestion, peak detection accuracy, matching logic, and full analysis pipeline integration.

---

## Bug Fixes & Changelog

### v1.1.0 — Pipeline accuracy and chart display

**`noise_filter.py`**
- Adaptive window selection: Savitzky-Golay window is now auto-capped to a 0.15° angular span, preventing over-smoothing of sharp SiC peaks. Previously a fixed `window=21` on 0.04°-step data attenuated the dominant 35.62° peak from 2273 → 1299 counts (57% retention). Now 98% retention.

**`peak_detector.py`**
- Thresholds now computed from `raw_intensity` (pre-smoothing) so weak peaks are not missed due to smoothed signal attenuation.
- Reported peak intensity now uses raw counts, not smoothed values.
- Column name resolution unified to handle both `two_theta`/`intensity` and `Angle`/`Intensity` headers.

**`peak_matcher.py`**
- Fixed one-to-one matching: experimental peaks are now consumed on assignment, preventing the same peak from matching multiple standard peaks and inflating confidence scores.

**`phase_identifier.py`**
- Residual angle comparison now uses ±0.01° tolerance instead of exact float equality, preventing rounding differences from generating false secondary phases.
- Duplicate-phase check now includes polytype, allowing 6H and 4H SiC to both be reported correctly.

**`similarity_engine.py`**
- Replaced hardcoded `λ = 1.5406` Å with `settings.WAVELENGTH_ANGSTROM` for d-spacing score consistency.

**`crystal_analyzer.py`**
- Added `polytype` as a dedicated field on `CrystalAnalysis` dataclass so the PDF report and API response can read it directly.

**`graph_generator.py`**
- Column name resolution added to `generate_all()` — no longer crashes on `Angle`/`Intensity` CSV headers.
- Overlay chart now uses `raw_intensity` maximum for standard peak height scaling.

**`report_generator.py`**
- Fixed `_build_crystal_info` — Polytype Designation row now correctly reads from `CrystalAnalysis.polytype` instead of always showing `—`.
- Fixed potential double-polytype string in `_build_summary`.
- Added `PageBreak` before the graphs section to prevent three stacked images overflowing the summary page.

**`analysis_routes.py`**
- `AnalysisResponse` now includes `full_intensity_raw` — the unsmoothed intensity array — for accurate frontend chart display.

**`XRDGraph.jsx` / `OverlayGraph.jsx`**
- Both charts now accept a `yMax` prop with `autorange: false` to pin the Y-axis ceiling to the true data maximum, preventing Plotly from clipping the axis during zoom.

**`ResultsPage.jsx`**
- Charts now receive `full_intensity_raw` (with `full_intensity` fallback) and a pre-computed `yMaxXRD`/`yMaxOverlay` value guarded against empty arrays.

### v1.2.0 — Authentication

- Added `LoginPage.jsx` with hardcoded single-user login and show/hide password toggle.
- Added `ProtectedRoute.jsx` — all routes except `/login` require authentication.
- `App.jsx` restructured so the Navbar/Sidebar shell is only rendered for authenticated sessions.
- Login state stored in `sessionStorage` (cleared on tab close).

---


## Running the System Permanently on Localhost (Windows)

The XRD Analysis System can run continuously in the background without keeping terminal windows open by using **PM2** as a process manager.

### Install PM2

Open Command Prompt as Administrator:

```bash
npm install -g pm2
```

---

## PM2 Configuration

Create a file named:

```text
ecosystem.config.js
```

in the project root directory:

```text
xrd-analysis-system/
```

Add the following configuration:

```js
module.exports = {
  apps: [
      { 
      name: "xrd-backend",
      script: "python",
      args: "-m uvicorn app:app --reload",
      cwd: "./backend",
      interpreter: "none",
    },
    {
      name: "xrd-frontend",
      script: "cmd",
      args: "/c npm run dev",
      cwd: "./frontend",
      interpreter: "none",
    },
  ],
};
```

---

## Start the System

From the project root:

```bash
pm2 start ecosystem.config.js
```

Check running services:

```bash
pm2 list
```

Expected output:

```text
xrd-backend     online
xrd-frontend    online
```

---

## Access the Application

| Service      | URL                        |
| ------------ | -------------------------- |
| Frontend     | http://localhost:5173      |
| Backend API  | http://localhost:8000      |
| Swagger Docs | http://localhost:8000/docs |

---

## Save Running Processes

```bash
pm2 save
```

---

## Auto-Start on Windows Login

Create a file:

```text
start_xrd_system.bat
```

Add:

```bat
@echo off

cd /d D:\xrd-analysis-system

pm2 resurrect
```

Press:

```text
Windows + R
```

Type:

```text
shell:startup
```

Place a shortcut of `start_xrd_system.bat` inside the Startup folder.

The XRD system will now automatically start in the background whenever Windows starts.

---

## Useful PM2 Commands

### View Running Apps

```bash
pm2 list
```

### Restart All Services

```bash
pm2 restart all
```

### Stop All Services

```bash
pm2 stop all
```

### Remove All Services

```bash
pm2 delete all
```


## Future Scope

- AI/ML-based phase prediction with neural networks
- Rietveld refinement for quantitative phase analysis
- Advanced peak indexing algorithms
- Cloud-based compound database (ICDD / COD integration)
- Multi-user authentication with role-based access control
- Mobile application
- Direct instrument integration (import from XRD hardware)

---

## Applications

- Materials Research
- Ceramics Analysis
- Nanomaterials Characterization
- Quality Control in Manufacturing
- Geology & Mineralogy
- Academic & Industrial Research

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.