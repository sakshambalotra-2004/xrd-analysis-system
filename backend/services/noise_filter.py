"""
services/noise_filter.py
========================
Noise Filtering Module — Stage 2 of the XRD analysis pipeline.

Applies signal smoothing to the raw intensity array so that the downstream
peak detector works on a cleaner signal without removing true peaks.

Supported methods
-----------------
- ``savitzky_golay``  (default) — Savitzky-Golay polynomial smoothing via
  ``scipy.signal.savgol_filter``.  Preserves peak positions and relative
  heights well for XRD data.
- ``gaussian``         — Gaussian kernel convolution via
  ``scipy.ndimage.gaussian_filter1d``.  Slightly more aggressive smoothing.
- ``moving_average``   — Simple uniform moving-average kernel.  Fastest but
  shifts peak positions at high noise levels.

=============================================================================
BUG FIX (adaptive window):
  The original fixed NOISE_FILTER_WINDOW (e.g. 21 points) was too wide for
  the sharp peaks common in SiC and HRXRD data.  A 21-point window on 0.04°-
  step data corresponds to 0.84° — far wider than the typical SiC FWHM of
  ~0.04–0.16°.  This caused severe peak attenuation (57 % retention for the
  35.62° SiC peak: 2273 raw → 1299 smoothed).

  The filter now auto-selects window_length based on data step-size:
    • Target smoothing span ≤ 0.15° (covers background noise without eating peaks)
    • Minimum window = polyorder + 2 (SciPy requirement)
    • Always odd
=============================================================================
"""

import logging

import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d
from scipy.signal import savgol_filter

from config import settings

logger = logging.getLogger(__name__)

FilterMethod = str  # Literal["savitzky_golay", "gaussian", "moving_average"]

# Maximum angular span (degrees) the smoothing window is allowed to cover.
# 0.15° is wide enough to suppress shot-noise but narrow enough to preserve
# FWHM of even the sharpest SiC Bragg reflections (~0.04–0.16°).
_MAX_SMOOTH_SPAN_DEG = 0.15


def _adaptive_window(angles: np.ndarray, requested_window: int, polyorder: int) -> int:
    """
    Return a window length that never exceeds _MAX_SMOOTH_SPAN_DEG in angular
    space, regardless of the value set in settings.

    Falls back gracefully to the settings value when the step size cannot be
    determined (e.g. fewer than 2 data points).
    """
    if len(angles) < 2:
        return requested_window

    step_deg = float(np.median(np.diff(angles)))
    if step_deg <= 0:
        return requested_window

    # How many points fit inside the max span?
    max_pts = int(_MAX_SMOOTH_SPAN_DEG / step_deg)
    max_pts = max(max_pts, polyorder + 2)   # SciPy: window must be > polyorder
    if max_pts % 2 == 0:
        max_pts -= 1                        # Must be odd for Savitzky-Golay

    # Use the smaller of the settings value and the span-limited value
    chosen = min(requested_window, max_pts)
    if chosen % 2 == 0:
        chosen -= 1
    chosen = max(chosen, polyorder + 2 if (polyorder + 2) % 2 == 1 else polyorder + 3)

    if chosen != requested_window:
        logger.info(
            "Adaptive SG window: settings=%d → capped to %d "
            "(step=%.4f°, max_span=%.2f°)",
            requested_window, chosen, step_deg, _MAX_SMOOTH_SPAN_DEG,
        )
    return chosen


class NoiseFilter:
    """
    Smooth the intensity column of an XRD DataFrame.

    Parameters
    ----------
    method : str
        One of 'savitzky_golay', 'gaussian', 'moving_average'.
    window : int
        Window length for Savitzky-Golay or moving-average smoothing (must
        be odd for Savitzky-Golay).  Defaults to ``settings.NOISE_FILTER_WINDOW``.
        This is treated as a *maximum* — the adaptive logic may reduce it to
        preserve sharp peaks.
    polyorder : int
        Polynomial order for Savitzky-Golay filter.
        Defaults to ``settings.NOISE_FILTER_POLYORDER``.
    sigma : float
        Standard deviation for the Gaussian kernel (in data-point units).
    """

    SUPPORTED_METHODS = ("savitzky_golay", "gaussian", "moving_average")

    def __init__(
        self,
        method: FilterMethod = "savitzky_golay",
        window: int | None = None,
        polyorder: int | None = None,
        sigma: float = 2.0,
    ) -> None:
        if method not in self.SUPPORTED_METHODS:
            raise ValueError(
                f"Unsupported filter method '{method}'. "
                f"Choose from: {self.SUPPORTED_METHODS}"
            )
        self.method = method
        self.window = window or settings.NOISE_FILTER_WINDOW
        self.polyorder = polyorder or settings.NOISE_FILTER_POLYORDER
        self.sigma = sigma

        # Ensure window is odd for Savitzky-Golay (static check; adaptive
        # check happens per-call when angles are available)
        if self.method == "savitzky_golay" and self.window % 2 == 0:
            self.window += 1
            logger.debug("Adjusted SG window to odd: %d", self.window)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Return a copy of *df* with the intensity column smoothed.

        Resolves column names flexibly (supports 'two_theta'/'Angle' and
        'intensity'/'Intensity').

        Parameters
        ----------
        df : pd.DataFrame
            Must contain an angle column and an intensity column.

        Returns
        -------
        pd.DataFrame
            Same shape as input; intensity column replaced with smoothed
            values.  Original raw intensity preserved in 'raw_intensity'.
        """
        df = df.copy()

        # ── Resolve column names ──────────────────────────────────────────
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

        angles = df[angle_col].to_numpy(dtype=np.float64)
        raw_intensity = df[intensity_col].to_numpy(dtype=np.float64)

        # ── Preserve raw values for chart display ─────────────────────────
        df["raw_intensity"] = raw_intensity.copy()

        # ── Apply adaptive smoothing ──────────────────────────────────────
        smoothed = self._smooth(raw_intensity, angles)
        df[intensity_col] = smoothed

        logger.info(
            "Noise filter applied (%s, effective_window=%d) — "
            "max intensity: raw=%.1f → smoothed=%.1f (%.1f %% retained)",
            self.method,
            self._last_window,
            raw_intensity.max(),
            smoothed.max(),
            smoothed.max() / raw_intensity.max() * 100 if raw_intensity.max() > 0 else 0,
        )
        return df

    def filter_array(self, intensity: np.ndarray, angles: np.ndarray | None = None) -> np.ndarray:
        """
        Smooth a 1-D intensity array and return the result.

        Parameters
        ----------
        intensity : np.ndarray
            Raw intensity values.
        angles : np.ndarray | None
            Corresponding 2θ angles.  When provided, the adaptive window
            logic activates and prevents over-smoothing sharp peaks.

        Returns
        -------
        np.ndarray
            Smoothed intensity values (same length, non-negative).
        """
        return self._smooth(np.asarray(intensity, dtype=np.float64), angles)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _smooth(self, intensity: np.ndarray, angles: np.ndarray | None) -> np.ndarray:
        """Core smoothing dispatcher. Sets self._last_window for logging."""
        self._last_window = self.window  # default; may be overridden below

        if self.method == "savitzky_golay":
            # ── Adaptive window selection ─────────────────────────────────
            if angles is not None and len(angles) == len(intensity):
                window = _adaptive_window(angles, self.window, self.polyorder)
            else:
                window = min(self.window, len(intensity))
                if window % 2 == 0:
                    window -= 1
                window = max(window, self.polyorder + 2)

            self._last_window = window
            smoothed = savgol_filter(
                intensity,
                window_length=window,
                polyorder=self.polyorder,
            )

        elif self.method == "gaussian":
            smoothed = gaussian_filter1d(intensity, sigma=self.sigma)

        elif self.method == "moving_average":
            kernel = np.ones(self.window) / self.window
            smoothed = np.convolve(intensity, kernel, mode="same")

        else:  # pragma: no cover
            smoothed = intensity.copy()

        # Clip negative artefacts produced by smoothing near zero-intensity regions
        return np.clip(smoothed, 0, None)