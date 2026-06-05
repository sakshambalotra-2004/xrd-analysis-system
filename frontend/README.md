# XRD Analysis System 🔬

A powerful, full-stack web application designed for the automated processing, phase identification, and visual comparison of X-Ray Diffraction (XRD) data. 

Built with a **FastAPI** Python engine for heavy mathematical processing and a responsive **React + Vite** frontend for interactive data visualization.

---

## ✨ Key Features

* **Automated Peak Detection:** Uses advanced SciPy signal processing (Savitzky-Golay filtering) to strip background noise and isolate precise diffraction peaks.
* **Crystallographic Phase Matching:** Compares experimental data against an integrated SQLite database to confidently identify compounds and specific polytypes (e.g., 6H, 15R, 3C).
* **Multi-Scan Comparison:** An interactive visualization dashboard powered by Plotly.js that allows users to overlay up to 3 diffractograms simultaneously to observe peak shifts and phase transformations.
* **Comprehensive PDF Reports:** Automatically generates multi-page, publication-ready PDF reports complete with matched peak tables, crystallite size calculations (Scherrer equation), and high-resolution graphs.
* **Data Persistence:** Keeps a local, easily accessible history of all uploaded scans and completed analyses.

---

## 🛠️ Technology Stack

**Frontend (User Interface)**
* **Framework:** React 18 powered by Vite
* **Routing:** React Router DOM
* **State Management:** TanStack React Query
* **Data Visualization:** Plotly.js (`react-plotly.js`)
* **Styling:** Custom CSS with a scientific, high-contrast palette

**Backend (Processing Engine)**
* **Framework:** FastAPI (Python 3.11+)
* **Data Processing:** Pandas, NumPy, SciPy
* **Document Generation:** ReportLab
* **Database:** SQLite

---

## 🚀 Getting Started

To run this application locally, you will need two terminal windows open—one for the backend API, and one for the frontend UI.

### 1. Start the Backend
The backend handles all mathematical calculations, database queries, and file generation.

```bash
# Navigate to the backend directory
cd backend

# Install required Python dependencies
pip install -r requirements.txt

# Start the FastAPI server with hot-reloading
python -m uvicorn app:app --reload