"""
services/peak_detector.py
==========================
Advanced Peak Detection Service — Adaptive detection for both 
standard Powder XRD and High-Resolution HRXRD Rocking Curves.
"""

import logging
import pandas as pd
import numpy as np
from scipy.signal import find_peaks, peak_widths

from config import settings

logger = logging.getLogger(__name__)

class PeakDetector:
    """Isolates significant diffraction peaks with scan-type awareness."""

    def detect(self, df_smooth: pd.DataFrame) -> pd.DataFrame:
        if df_smooth.empty:
            logger.warning("Empty dataframe passed to PeakDetector.")
            return pd.DataFrame(columns=["two_theta", "intensity", "fwhm_deg", "prominence"])

        angle_col = 'Angle' if 'Angle' in df_smooth.columns else df_smooth.columns[0]
        intensity_col = 'Intensity' if 'Intensity' in df_smooth.columns else df_smooth.columns[1]

        angles = df_smooth[angle_col].to_numpy()
        intensities = df_smooth[intensity_col].to_numpy()

        global_max = float(np.max(intensities))
        if global_max <= 0:
            global_max = 1.0

        # ── ADAPTIVE SENSITIVITY LOGIC ───────────────────────────────────────
        # HRXRD Rocking Curves are extremely narrow (<1° range).
        # Standard Powder XRD scans are wide (>20° range).
        scan_range = float(np.max(angles) - np.min(angles))
        
        if scan_range < 1.0:
            # HRXRD Mode: Use ultra-low thresholds to capture sharp peaks
            height_fraction = 0.005  # 0.5% threshold
            prominence_fraction = 0.005
            min_dist = 5 # Narrow distance for fine rocking curve peaks
        else:
            # Powder XRD Mode: Use standard 5% thresholds
            height_fraction = getattr(settings, "PEAK_HEIGHT_THRESHOLD", 0.05)
            prominence_fraction = getattr(settings, "PEAK_PROMINENCE_FRACTION", 0.05)
            min_dist = settings.PEAK_MIN_DISTANCE

        abs_height = global_max * height_fraction
        abs_prominence = global_max * prominence_fraction

        logger.info(
            "Detecting peaks | Range: %.2f° | Height Limit: %.2f | Prominence: %.2f",
            scan_range, abs_height, abs_prominence
        )

        # Execute Scipy peak detector
        peak_indices, properties = find_peaks(
            intensities,
            height=abs_height,
            prominence=abs_prominence,
            distance=min_dist
        )

        if len(peak_indices) == 0:
            logger.info("No peaks passed validation constraints.")
            return pd.DataFrame(columns=["two_theta", "intensity", "fwhm_deg", "prominence"])

        # ── CALCULATE FWHM ──────────────────────────────────────────────────
        # rel_height=0.5 measures width exactly at the Half-Maximum
        widths_results = peak_widths(intensities, peak_indices, rel_height=0.5)
        widths_in_points = widths_results[0]
        
        # Calculate step size with high precision
        step_size = float(np.median(np.diff(angles)))
        fwhm_degrees = widths_in_points * step_size

        # Build results matrix
        detected_peaks_list = []
        for i, idx in enumerate(peak_indices):
            detected_peaks_list.append({
                "two_theta": float(angles[idx]),
                "intensity": float(intensities[idx]),
                "fwhm_deg": float(fwhm_degrees[i]),
                "prominence": float(properties["prominences"][i])
            })

        peaks_df = pd.DataFrame(detected_peaks_list)
        
        # Sort by intensity descending
        peaks_df = peaks_df.sort_values(by="intensity", ascending=False).reset_index(drop=True)
        
        logger.info("Detected %d peaks.", len(peaks_df))
        return peaks_df