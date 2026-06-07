"""
services/peak_detector.py
==========================
Advanced Peak Detection Service — Adaptive detection for both 
standard Powder XRD and High-Resolution HRXRD Rocking Curves.

FIX SUMMARY
-----------
1. Column name resolution: now checks both 'two_theta'/'intensity' (noise_filter
   output) AND 'Angle'/'Intensity' (raw CSV output) — consistent with the rest
   of the pipeline.

2. global_max for threshold calculation now uses raw_intensity when available
   (stored by noise_filter in the 'raw_intensity' column).  Previously, thresholds
   were computed against the smoothed max, which was ~57% of the true peak height
   due to over-smoothing — causing weak peaks to be missed entirely.

3. FWHM is calculated on the smoothed signal (correct — smoother = more stable
   width estimate) but peak intensity reported back uses raw_intensity at that
   index so the output table and chart markers show true counts, not smoothed.
"""

import logging
import pandas as pd
import numpy as np
from scipy.signal import find_peaks, peak_widths

from config import settings

logger = logging.getLogger(__name__)


def _resolve_cols(df: pd.DataFrame) -> tuple[str, str]:
    """Return (angle_col, intensity_col) regardless of naming convention."""
    angle_col = (
        "two_theta" if "two_theta" in df.columns
        else "Angle" if "Angle" in df.columns
        else df.columns[0]
    )
    intensity_col = (
        "intensity" if "intensity" in df.columns
        else "Intensity" if "Intensity" in df.columns
        else df.columns[1]
    )
    return angle_col, intensity_col


class PeakDetector:
    """Isolates significant diffraction peaks with scan-type awareness."""

    def detect(self, df_smooth: pd.DataFrame) -> pd.DataFrame:
        if df_smooth.empty:
            logger.warning("Empty dataframe passed to PeakDetector.")
            return pd.DataFrame(columns=["two_theta", "intensity", "fwhm_deg", "prominence"])

        angle_col, intensity_col = _resolve_cols(df_smooth)

        angles      = df_smooth[angle_col].to_numpy(dtype=np.float64)
        intensities = df_smooth[intensity_col].to_numpy(dtype=np.float64)   # smoothed — used for peak finding & FWHM

        # FIX: use raw intensity for threshold so weak peaks aren't missed when
        # the smoothed signal is attenuated.  noise_filter stores it in 'raw_intensity'.
        if "raw_intensity" in df_smooth.columns:
            raw_intensities = df_smooth["raw_intensity"].to_numpy(dtype=np.float64)
            logger.info("Using raw_intensity column for threshold calculation.")
        else:
            raw_intensities = intensities   # fallback: no raw available
            logger.info("raw_intensity column not found; using smoothed for thresholds.")

        global_max = float(np.max(raw_intensities))
        if global_max <= 0:
            global_max = 1.0

        # ── ADAPTIVE SENSITIVITY LOGIC ───────────────────────────────────
        scan_range = float(np.max(angles) - np.min(angles))

        if scan_range < 1.0:
            # HRXRD Rocking Curve: ultra-low thresholds, narrow distance
            height_fraction     = 0.005
            prominence_fraction = 0.005
            min_dist            = 5
        else:
            # Standard Powder XRD
            height_fraction     = getattr(settings, "PEAK_HEIGHT_THRESHOLD",    0.05)
            prominence_fraction = getattr(settings, "PEAK_PROMINENCE_FRACTION", 0.05)
            min_dist            = settings.PEAK_MIN_DISTANCE

        abs_height     = global_max * height_fraction
        abs_prominence = global_max * prominence_fraction

        logger.info(
            "Detecting peaks | Range: %.2f° | Raw max: %.1f | "
            "Height thresh: %.1f | Prominence thresh: %.1f",
            scan_range, global_max, abs_height, abs_prominence,
        )

        # ── PEAK FINDING (on smoothed signal for stability) ───────────────
        peak_indices, properties = find_peaks(
            intensities,
            height=abs_height,
            prominence=abs_prominence,
            distance=min_dist,
        )

        if len(peak_indices) == 0:
            logger.info("No peaks passed validation constraints.")
            return pd.DataFrame(columns=["two_theta", "intensity", "fwhm_deg", "prominence"])

        # ── FWHM (on smoothed signal — more stable width estimate) ────────
        widths_results  = peak_widths(intensities, peak_indices, rel_height=0.5)
        widths_in_points = widths_results[0]
        step_size        = float(np.median(np.diff(angles)))
        fwhm_degrees     = widths_in_points * step_size

        # ── BUILD OUTPUT ──────────────────────────────────────────────────
        detected_peaks_list = []
        for i, idx in enumerate(peak_indices):
            detected_peaks_list.append({
                "two_theta":  float(angles[idx]),
                # FIX: report true (raw) intensity at the peak position so the
                # chart markers and output table show actual counts, not the
                # smoothed (attenuated) value.
                "intensity":  float(raw_intensities[idx]),
                "fwhm_deg":   float(fwhm_degrees[i]),
                "prominence": float(properties["prominences"][i]),
            })

        peaks_df = (
            pd.DataFrame(detected_peaks_list)
            .sort_values(by="intensity", ascending=False)
            .reset_index(drop=True)
        )

        logger.info("Detected %d peaks.", len(peaks_df))
        return peaks_df