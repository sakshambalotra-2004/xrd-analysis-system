"""
utils/math_utils.py
====================
Mathematical utility functions for the XRD Analysis System.

Covers peak profile fitting, background subtraction, FWHM estimation,
statistical helpers, and unit conversion functions.
"""

import math
from typing import Tuple

import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import find_peaks


# ---------------------------------------------------------------------------
# Peak profile functions
# ---------------------------------------------------------------------------

def gaussian(x: np.ndarray, amplitude: float, center: float, sigma: float) -> np.ndarray:
    """
    Gaussian peak profile.

        f(x) = A · exp(−(x − μ)² / (2σ²))

    Parameters
    ----------
    x         : array of x values
    amplitude : peak height A
    center    : peak centre μ
    sigma     : standard deviation σ

    Returns
    -------
    np.ndarray : Gaussian-evaluated values
    """
    return amplitude * np.exp(-((x - center) ** 2) / (2 * sigma ** 2))


def lorentzian(x: np.ndarray, amplitude: float, center: float, gamma: float) -> np.ndarray:
    """
    Lorentzian (Cauchy) peak profile.

        f(x) = A · (γ²) / ((x − x₀)² + γ²)

    Parameters
    ----------
    x         : array of x values
    amplitude : peak height A
    center    : peak centre x₀
    gamma     : half-width at half-maximum γ
    """
    return amplitude * (gamma ** 2) / ((x - center) ** 2 + gamma ** 2)


def pseudo_voigt(
    x: np.ndarray,
    amplitude: float,
    center: float,
    sigma: float,
    eta: float,
) -> np.ndarray:
    """
    Pseudo-Voigt profile: linear combination of Gaussian and Lorentzian.

        f(x) = η · L(x) + (1 − η) · G(x)

    Parameters
    ----------
    eta : float
        Mixing parameter in [0, 1].  eta=0 → pure Gaussian, eta=1 → pure Lorentzian.
    """
    eta = np.clip(eta, 0.0, 1.0)
    g = gaussian(x, amplitude, center, sigma)
    l = lorentzian(x, amplitude, center, sigma)
    return eta * l + (1 - eta) * g


# ---------------------------------------------------------------------------
# FWHM estimation
# ---------------------------------------------------------------------------

def fwhm_from_sigma(sigma: float) -> float:
    """Convert Gaussian σ to FWHM: FWHM = 2√(2 ln 2) · σ ≈ 2.3548 σ."""
    return 2.0 * math.sqrt(2.0 * math.log(2.0)) * sigma


def sigma_from_fwhm(fwhm: float) -> float:
    """Convert FWHM to Gaussian σ: σ = FWHM / (2√(2 ln 2))."""
    return fwhm / (2.0 * math.sqrt(2.0 * math.log(2.0)))


def estimate_fwhm_direct(x: np.ndarray, y: np.ndarray, peak_idx: int) -> float:
    """
    Estimate FWHM directly by linear interpolation around a peak.

    Parameters
    ----------
    x         : 1-D array of x values (e.g. 2θ)
    y         : 1-D array of y values (intensity)
    peak_idx  : index of the peak in x/y arrays

    Returns
    -------
    float : estimated FWHM in units of x, or 0.0 if estimation fails.
    """
    try:
        half_max = y[peak_idx] / 2.0
        # Left side
        left = peak_idx - 1
        while left > 0 and y[left] > half_max:
            left -= 1
        # Right side
        right = peak_idx + 1
        while right < len(y) - 1 and y[right] > half_max:
            right += 1
        return float(x[right] - x[left])
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Background subtraction
# ---------------------------------------------------------------------------

def linear_background(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """
    Subtract a linear background estimated from the endpoints of the array.

    Returns
    -------
    np.ndarray : background-subtracted intensities (clipped to ≥ 0).
    """
    x0, x1 = x[0], x[-1]
    y0, y1 = y[0], y[-1]
    if x1 == x0:
        return np.clip(y - y0, 0, None)
    slope = (y1 - y0) / (x1 - x0)
    background = y0 + slope * (x - x0)
    return np.clip(y - background, 0, None)


def rolling_minimum_background(y: np.ndarray, window: int = 50) -> np.ndarray:
    """
    Estimate background using a rolling minimum (Sonneveld & Visser algorithm).

    Returns background-subtracted intensities.
    """
    n = len(y)
    half = window // 2
    background = np.zeros(n)
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half)
        background[i] = y[lo:hi].min()
    return np.clip(y - background, 0, None)


# ---------------------------------------------------------------------------
# Statistical helpers
# ---------------------------------------------------------------------------

def normalise_intensity(intensity: np.ndarray) -> np.ndarray:
    """Normalise intensity array to [0, 100] range."""
    max_val = intensity.max()
    if max_val == 0:
        return intensity.copy()
    return (intensity / max_val) * 100.0


def relative_intensity(intensity: np.ndarray) -> np.ndarray:
    """Return relative intensities scaled so the strongest peak = 100."""
    return normalise_intensity(intensity)


def r_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Coefficient of determination R² for profile fit quality."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return float(1 - ss_res / ss_tot) if ss_tot != 0 else 0.0


# ---------------------------------------------------------------------------
# Unit conversion
# ---------------------------------------------------------------------------

def angstrom_to_nm(value: float) -> float:
    """Convert Ångströms to nanometres."""
    return value / 10.0


def nm_to_angstrom(value: float) -> float:
    """Convert nanometres to Ångströms."""
    return value * 10.0


def deg_to_rad(deg: float) -> float:
    return math.radians(deg)


def rad_to_deg(rad: float) -> float:
    return math.degrees(rad)