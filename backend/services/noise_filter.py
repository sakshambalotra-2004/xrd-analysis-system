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

Usage:
    from services.noise_filter import NoiseFilter

    nf = NoiseFilter(method="savitzky_golay")
    smoothed_df = nf.filter(df)          # df has columns two_theta, intensity
    smoothed_intensity = nf.filter_array(intensity_array)
"""

import logging

import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d
from scipy.signal import savgol_filter

from config import settings

logger = logging.getLogger(__name__)

FilterMethod = str  # Literal["savitzky_golay", "gaussian", "moving_average"]


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

        # Ensure window is odd for Savitzky-Golay
        if self.method == "savitzky_golay" and self.window % 2 == 0:
            self.window += 1
            logger.debug("Adjusted SG window to odd: %d", self.window)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Return a copy of *df* with the intensity column smoothed.

        Parameters
        ----------
        df : pd.DataFrame
            Must contain columns 'two_theta' and 'intensity'.

        Returns
        -------
        pd.DataFrame
            Same shape as input; 'intensity' replaced with smoothed values.
            Original raw intensity preserved in 'raw_intensity'.
        """
        df = df.copy()
        df["raw_intensity"] = df["intensity"].copy()
        df["intensity"] = self.filter_array(df["intensity"].to_numpy())
        logger.info(
            "Noise filter applied (%s, window=%d) — max intensity: raw=%.1f, smoothed=%.1f",
            self.method,
            self.window,
            df["raw_intensity"].max(),
            df["intensity"].max(),
        )
        return df

    def filter_array(self, intensity: np.ndarray) -> np.ndarray:
        """
        Smooth a 1-D intensity array and return the result.

        Parameters
        ----------
        intensity : np.ndarray
            Raw intensity values.

        Returns
        -------
        np.ndarray
            Smoothed intensity values (same length, non-negative).
        """
        intensity = np.asarray(intensity, dtype=np.float64)

        if self.method == "savitzky_golay":
            # Cap window to array length
            window = min(self.window, len(intensity))
            if window % 2 == 0:
                window -= 1
            window = max(window, self.polyorder + 2)  # polyorder < window required
            smoothed = savgol_filter(intensity, window_length=window, polyorder=self.polyorder)

        elif self.method == "gaussian":
            smoothed = gaussian_filter1d(intensity, sigma=self.sigma)

        elif self.method == "moving_average":
            kernel = np.ones(self.window) / self.window
            smoothed = np.convolve(intensity, kernel, mode="same")

        else:  # pragma: no cover
            smoothed = intensity.copy()

        # Clip negative artefacts produced by smoothing near zero-intensity regions
        smoothed = np.clip(smoothed, 0, None)
        return smoothed