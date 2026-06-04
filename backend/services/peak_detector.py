"""
services/peak_detector.py
==========================
Advanced Peak Detection Service — Filters out minor statistical noise 
and isolates diffraction peaks matching the 5% maximum intensity rule.
"""

import logging
import pandas as pd
import numpy as np
from scipy.signal import find_peaks

from config import settings

logger = logging.getLogger(__name__)

class PeakDetector:
    """Isolates significant diffraction peaks from smoothed background matrix curves."""

    def detect(self, df_smooth: pd.DataFrame) -> pd.DataFrame:
        if df_smooth.empty:
            logger.warning("Empty dataframe passed to PeakDetector.")
            return pd.DataFrame(columns=["two_theta", "intensity", "fwhm_deg", "prominence"])

        angle_col = 'Angle' if 'Angle' in df_smooth.columns else df_smooth.columns[0]
        intensity_col = 'Intensity' if 'Intensity' in df_smooth.columns else df_smooth.columns[1]

        angles = df_smooth[angle_col].to_numpy()
        intensities = df_smooth[intensity_col].to_numpy()

        # Find the absolute highest intensity value in this specific file
        global_max = float(np.max(intensities))
        if global_max <= 0:
            global_max = 1.0

        # Safely retrieve configuration keys with fallback options
        height_threshold_fraction = getattr(settings, "PEAK_HEIGHT_THRESHOLD", 0.05)
        prominence_threshold_fraction = getattr(settings, "PEAK_PROMINENCE_FRACTION", getattr(settings, "PEAK_PROMINENCE", 0.05))

        # Apply the 5% of max intensity rule
        absolute_height_limit = global_max * height_threshold_fraction
        absolute_prominence_limit = global_max * prominence_threshold_fraction

        logger.info(
            "Running 5%% Peak Filtering: Global Max=%.1f, Cutoff Height=%.1f, Cutoff Prominence=%.1f",
            global_max, absolute_height_limit, absolute_prominence_limit
        )

        # Execute Scipy peak detector using your exact 5% thresholds
        peak_indices, properties = find_peaks(
            intensities,
            height=absolute_height_limit,
            prominence=absolute_prominence_limit,
            distance=settings.PEAK_MIN_DISTANCE
        )

        if len(peak_indices) == 0:
            logger.info("No peaks passed the 5% maximum intensity validation constraints.")
            return pd.DataFrame(columns=["two_theta", "intensity", "fwhm_deg", "prominence"])

        # Calculate Full Width at Half Maximum (FWHM)
        from scipy.signal import peak_widths
        widths_results = peak_widths(intensities, peak_indices, rel_height=0.5)
        widths_in_points = widths_results[0]

        # Convert step indexes back to physical degrees 2-Theta
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
        
        # Sort rows by intensity descending
        peaks_df = peaks_df.sort_values(by="intensity", ascending=False).reset_index(drop=True)
        
        logger.info("Successfully verified %d peaks crossing the 5%% threshold rule.", len(peaks_df))
        return peaks_df