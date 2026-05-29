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
- [Testing](#testing)
- [Future Scope](#future-scope)
- [Applications](#applications)
- [License](#license)

---

## Overview

The XRD Compound Identification and Analysis System automates the process of identifying crystalline compounds from X-ray diffraction data. A user uploads a CSV file containing 2θ (two-theta) angle and intensity measurements; the system then:

1. Filters noise from the raw signal
2. Detects and selects significant peaks
3. Matches peaks to a standard compound database using d-spacing and Bragg's Law
4. Computes similarity scores and confidence levels
5. Retrieves crystallographic information (space group, Miller indices, etc.)
6. Generates overlay graphs and downloadable PDF reports

---

## Features

- **Automated Peak Detection** — Identifies significant peaks from noisy XRD patterns
- **Phase Identification** — Matches experimental peaks to known compound standards
- **Crystallite Size Analysis** — Applies the Scherrer Equation: `D = Kλ / β cos θ`
- **d-Spacing Calculation** — Uses Bragg's Law: `nλ = 2d sin θ`
- **Peak Shift Analysis** — Detects strain, stress, doping, and thermal effects
- **Multi-Phase Detection** — Identifies multiple compounds within a single sample
- **Peak Indexing** — Assigns Miller indices (h, k, l) automatically
- **Overlay Visualization** — Side-by-side comparison of experimental vs. standard patterns
- **PDF Report Generation** — Produces tables, graphs, and crystallographic summaries
- **ML-Based Prediction** — Optional machine learning predictor for crystal system classification

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

### Workflow

| Step | Module | Description |
|------|--------|-------------|
| 1 | CSV Reader | Ingest and validate experimental data via Pandas |
| 2 | Noise Filter | Smooth signal using Savitzky-Golay or Gaussian filters |
| 3 | Peak Detector | Select peaks above adaptive threshold |
| 4 | Peak Matching Engine | Compare 2θ values against standard database (tolerance ±0.2°) |
| 5 | Similarity Scoring | Compute confidence: `Score = (Matched Peaks / Total Standard Peaks) × 100` |
| 6 | Compound Identification | Predict compound name, formula, and crystal system |
| 7 | Crystal Info Retrieval | Fetch hkl indices, d-spacing, space group from database |
| 8 | Graph Visualization | Generate experimental, standard, and overlay charts |
| 9 | Analysis Module | Calculate crystallite size, peak shift, detected phases |
| 10 | Report Output | Render PDF with tables, graphs, and analysis summary |

---

## Project Structure

```
xrd-analysis-system/
├── backend/
│   ├── app.py                    # FastAPI application entry point
│   ├── config.py                 # Environment configuration
│   ├── requirements.txt          # Python dependencies
│   ├── routes/
│   │   ├── upload_routes.py      # File upload endpoints
│   │   ├── analysis_routes.py    # Analysis trigger endpoints
│   │   └── report_routes.py      # Report download endpoints
│   ├── services/
│   │   ├── csv_reader.py         # CSV ingestion and validation
│   │   ├── noise_filter.py       # Signal smoothing
│   │   ├── peak_detector.py      # Peak detection algorithm
│   │   ├── peak_matcher.py       # Database matching logic
│   │   ├── similarity_engine.py  # Confidence scoring
│   │   ├── crystal_analyzer.py   # Crystallographic computations
│   │   ├── d_spacing_calculator.py
│   │   ├── phase_identifier.py
│   │   ├── graph_generator.py    # Chart/overlay generation
│   │   ├── report_generator.py   # PDF report builder
│   │   └── ml_predictor.py       # ML crystal system classifier
│   ├── database/
│   │   ├── standards/            # JSON files per compound (sio2.json, sic.json, …)
│   │   ├── experimental_data/    # Uploaded CSV files (persisted)
│   │   └── sqlite/xrd_database.db
│   ├── models/
│   │   ├── trained_model.pkl
│   │   ├── scaler.pkl
│   │   └── label_encoder.pkl
│   ├── utils/
│   │   ├── file_handler.py
│   │   ├── peak_utils.py
│   │   ├── graph_utils.py
│   │   ├── math_utils.py
│   │   ├── validation.py
│   │   └── constants.py
│   ├── reports/
│   │   ├── pdf_reports/
│   │   ├── graphs/
│   │   └── overlay_images/
│   └── uploads/
│       ├── csv/
│       └── temp/
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── public/
│   └── src/
│       ├── pages/                # Dashboard, Upload, Results, Analysis, Reports
│       ├── components/           # Navbar, XRDGraph, PeakTable, ConfidenceCard, …
│       ├── charts/               # Experimental, Standard, Overlay, PeakShift charts
│       ├── api/                  # uploadApi, analysisApi, reportApi
│       └── styles/
│
├── datasets/
│   ├── raw_xrd_patterns/
│   ├── processed_patterns/
│   └── training_data/
│
├── tests/
│   ├── test_csv_reader.py
│   ├── test_peak_detector.py
│   ├── test_matcher.py
│   └── test_analysis.py
│
├── documentation/
│   ├── system_design.pdf
│   ├── api_documentation.pdf
│   └── workflow.png
│
├── README.md
├── LICENSE
└── .gitignore
```

---

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+

### Backend

```bash
# Clone the repository
git clone https://github.com/your-org/xrd-analysis-system.git
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

1. Navigate to **Upload CSV** in the sidebar.
2. Choose a CSV file with columns `2theta (°)` and `Intensity`.
3. Click **Analyze** — the system will process the file through all 10 pipeline stages.
4. View results on the **Results** page: best match compound, confidence score, peak match table.
5. Explore detailed crystallographic data on the **Analysis** page.
6. Download the full **PDF Report** from the Reports page.

### Input CSV Format

```
2theta (°), Intensity
20.543,     40
26.347,     100
35.922,     10
39.081,     6
...
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload CSV file |
| GET | `/api/analysis/{file_id}` | Run full analysis pipeline |
| GET | `/api/results/{file_id}` | Retrieve analysis results |
| GET | `/api/report/{file_id}` | Download PDF report |
| GET | `/api/compounds` | List all standard compounds |
| GET | `/api/health` | Health check |

Full API documentation is available at `http://localhost:8000/docs` (Swagger UI).

---

## Database Schema

### Standard Compound JSON

```json
{
  "compound_name": "Silicon Carbide",
  "formula": "SiC",
  "crystal_system": "Hexagonal",
  "space_group": "P63mc",
  "peaks": [
    { "two_theta": 35.60, "d": 2.52, "intensity": 100, "h": 1, "k": 0, "l": 1 },
    { "two_theta": 41.40, "d": 2.17, "intensity": 60,  "h": 1, "k": 0, "l": 2 }
  ]
}
```

### SQLite Tables

- `experiments` — uploaded file metadata, timestamps, file paths
- `analysis_results` — matched compound, confidence score, crystallite size, peak shift
- `peaks` — detected peaks per experiment (2θ, d, intensity, hkl)
- `compounds` — cached standard compound index

---

## Analysis Capabilities

| Capability | Method |
|------------|--------|
| Phase Identification | Peak matching + similarity scoring |
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

Similarity score:

```
Score = (Matched Peaks / Total Standard Peaks) × 100
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, Plotly.js, Tailwind CSS |
| Backend | Python, FastAPI |
| Data Processing | Pandas, NumPy, SciPy |
| Visualization | Matplotlib, Plotly |
| Machine Learning | scikit-learn |
| Database | JSON files, SQLite, MongoDB (optional) |
| Report Generation | ReportLab / WeasyPrint |

---

## Configuration

See [`config.py`](backend/config.py) for all configurable parameters including upload limits, peak detection thresholds, matching tolerance, wavelength, and database paths.

Copy `.env.example` to `.env` and adjust values as needed.

---

## Testing

```bash
cd backend
pytest tests/ -v
```

Test modules cover CSV ingestion, peak detection accuracy, matching logic, and full analysis pipeline integration.

---

## Future Scope

- AI/ML-based phase prediction with neural networks
- Rietveld refinement for quantitative phase analysis
- Advanced peak indexing algorithms
- Cloud-based compound database (ICDD / COD integration)
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