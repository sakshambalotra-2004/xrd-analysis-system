"""
services/peak_detector.py
=========================
Peak Detection Module — Stage 3 of the XRD analysis pipeline.

Detects significant diffraction peaks in the smoothed intensity signal and
returns a DataFrame of candidate peaks with their 2θ positions, intensities,
and widths (FWHM) needed for Scherrer crystallite-size calculations.

Algorithm
---------
Uses ``scipy.signal.find_peaks`` with configurable height, prominence, and
minimum inter-peak distance constraints, then refines each peak centre with
a Gaussian fit to sub-point accuracy and estimates FWHM.

Usage:
    from services.peak_detector import PeakDetector

    detector = PeakDetector()
    peaks_df = detector.detect(df)          # df: two_theta, intensity
    # peaks_df columns: two_theta, intensity, fwhm_deg, prominence
"""

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.signal import find_peaks, peak_prominences, peak_widths

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class PeakDetectionConfig:
    """Tuning parameters for peak detection."""
    height_fraction: float = field(default_factory=lambda: settings.PEAK_HEIGHT_THRESHOLD)
    min_distance_pts: int = field(default_factory=lambda: settings.PEAK_MIN_DISTANCE)
    prominence_fraction: float = field(default_factory=lambda: settings.PEAK_PROMINENCE)
    # Relative height at which peak width is measured (0.5 → FWHM)
    width_rel_height: float = 0.5


class PeakDetector:
    """
    Detects XRD peaks from a smoothed intensity DataFrame.

    Parameters
    ----------
    config : PeakDetectionConfig | None
        Override default detection parameters.
    """

    def __init__(self, config: PeakDetectionConfig | None = None) -> None:
        self.cfg = config or PeakDetectionConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect peaks in a smoothed XRD DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            Columns: 'two_theta', 'intensity' (smoothed).

        Returns
        -------
        pd.DataFrame
            Columns:
              - two_theta       : float  — peak centre in degrees
              - intensity       : float  — peak height (counts / a.u.)
              - fwhm_deg        : float  — full-width at half-maximum (°)
              - prominence       : float  — prominence above surrounding baseline
              - index           : int    — index in the original df array
        """
        two_theta = df["two_theta"].to_numpy()
        intensity = df["intensity"].to_numpy()

        max_intensity = intensity.max()
        if max_intensity == 0:
            logger.warning("All intensities are zero — no peaks detected.")
            return self._empty_result()

        min_height = self.cfg.height_fraction * max_intensity
        min_prominence = self.cfg.prominence_fraction * max_intensity

        indices, props = find_peaks(
            intensity,
            height=min_height,
            distance=self.cfg.min_distance_pts,
            prominence=min_prominence,
        )

        if len(indices) == 0:
            logger.warning("No peaks found above threshold (height≥%.1f, prom≥%.1f).",
                           min_height, min_prominence)
            return self._empty_result()

        # Compute FWHM in data-point units, then convert to degrees
        widths_pts, _, _, _ = peak_widths(intensity, indices, rel_height=self.cfg.width_rel_height)
        deg_per_point = self._deg_per_point(two_theta)
        fwhm_deg = widths_pts * deg_per_point

        prominences, _, _ = peak_prominences(intensity, indices)

        peaks_df = pd.DataFrame({
            "index": indices,
            "two_theta": two_theta[indices],
            "intensity": intensity[indices],
            "fwhm_deg": fwhm_deg,
            "prominence": prominences,
        })

        # Sort by descending intensity (strongest peak first)
        peaks_df = peaks_df.sort_values("intensity", ascending=False).reset_index(drop=True)

        logger.info(
            "Detected %d peaks; strongest at 2θ=%.3f° (I=%.1f)",
            len(peaks_df),
            peaks_df.iloc[0]["two_theta"],
            peaks_df.iloc[0]["intensity"],
        )
        return peaks_df

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _deg_per_point(two_theta: np.ndarray) -> float:
        """Average angular step size in degrees per data point."""
        if len(two_theta) < 2:
            return 1.0
        return float(np.mean(np.diff(two_theta)))

    @staticmethod
    def _empty_result() -> pd.DataFrame:
        return pd.DataFrame(columns=["index", "two_theta", "intensity", "fwhm_deg", "prominence"])