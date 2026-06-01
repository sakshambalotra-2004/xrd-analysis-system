"""
services/d_spacing_calculator.py
=================================
d-Spacing Calculator — dedicated service for Bragg's Law calculations.

Provides both scalar and vectorised d-spacing computation plus the inverse
(2θ from d-spacing), and utility functions for comparing experimental
d-spacings against a standard compound.

Physics
-------
Bragg's Law (first order, n = 1):

    λ = 2 d sin θ   →   d = λ / (2 sin θ)

where θ is the Bragg angle (half of the measured 2θ), λ is the X-ray
wavelength in Ångströms.

Usage:
    from services.d_spacing_calculator import DSpacingCalculator

    calc = DSpacingCalculator()
    d = calc.from_two_theta(26.64)          # → 3.34 Å
    two_theta = calc.to_two_theta(3.34)     # → 26.64°
    df = calc.compute_for_dataframe(peaks_df)
"""

import logging
import math

import numpy as np
import pandas as pd

from config import settings

logger = logging.getLogger(__name__)


class DSpacingCalculationError(ValueError):
    """Raised for unphysical inputs (e.g. θ = 0 or θ ≥ 90°)."""


class DSpacingCalculator:
    """
    Bragg's Law d-spacing calculator.

    Parameters
    ----------
    wavelength_A : float
        X-ray wavelength in Ångströms. Defaults to ``settings.WAVELENGTH_ANGSTROM``.
    n : int
        Diffraction order. Default 1.
    """

    def __init__(
        self,
        wavelength_A: float | None = None,
        n: int | None = None,
    ) -> None:
        self.lam = wavelength_A or settings.WAVELENGTH_ANGSTROM
        self.n = n or settings.BRAGG_ORDER

    # ------------------------------------------------------------------
    # Scalar API
    # ------------------------------------------------------------------

    def from_two_theta(self, two_theta_deg: float) -> float:
        """
        Calculate d-spacing from a 2θ angle.

        Parameters
        ----------
        two_theta_deg : float
            Measured 2θ in degrees (0 < 2θ < 180).

        Returns
        -------
        float
            d-spacing in Ångströms, rounded to 4 decimal places.

        Raises
        ------
        DSpacingCalculationError
            If two_theta_deg ≤ 0 or ≥ 180.
        """
        if not (0 < two_theta_deg < 180):
            raise DSpacingCalculationError(
                f"2θ must be in (0°, 180°); got {two_theta_deg}°."
            )
        theta_rad = math.radians(two_theta_deg / 2.0)
        sin_theta = math.sin(theta_rad)
        return round((self.n * self.lam) / (2.0 * sin_theta), 4)

    def to_two_theta(self, d_spacing_A: float) -> float:
        """
        Calculate the 2θ angle for a given d-spacing.

        Parameters
        ----------
        d_spacing_A : float
            d-spacing in Ångströms.

        Returns
        -------
        float
            2θ in degrees, rounded to 4 decimal places.

        Raises
        ------
        DSpacingCalculationError
            If d_spacing_A is too small (sin θ would exceed 1).
        """
        if d_spacing_A <= 0:
            raise DSpacingCalculationError(
                f"d-spacing must be positive; got {d_spacing_A} Å."
            )
        sin_theta = (self.n * self.lam) / (2.0 * d_spacing_A)
        if sin_theta > 1.0:
            raise DSpacingCalculationError(
                f"d-spacing {d_spacing_A} Å is too small for λ={self.lam} Å "
                f"(sin θ = {sin_theta:.4f} > 1)."
            )
        theta_rad = math.asin(sin_theta)
        return round(math.degrees(2.0 * theta_rad), 4)

    # ------------------------------------------------------------------
    # Vectorised API
    # ------------------------------------------------------------------

    def from_two_theta_array(self, two_theta: np.ndarray) -> np.ndarray:
        """
        Vectorised Bragg's Law over a NumPy array.

        Returns
        -------
        np.ndarray
            d-spacing values in Ångströms; invalid entries become NaN.
        """
        two_theta = np.asarray(two_theta, dtype=np.float64)
        valid = (two_theta > 0) & (two_theta < 180)
        theta_rad = np.where(valid, np.radians(two_theta / 2.0), np.nan)
        sin_theta = np.sin(theta_rad)
        d = np.where(valid & (sin_theta > 0), (self.n * self.lam) / (2.0 * sin_theta), np.nan)
        return np.round(d, 4)

    # ------------------------------------------------------------------
    # DataFrame utility
    # ------------------------------------------------------------------

    def compute_for_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add a 'd_spacing' column to a DataFrame that contains 'two_theta'.

        Parameters
        ----------
        df : pd.DataFrame
            Must contain column 'two_theta'.

        Returns
        -------
        pd.DataFrame
            Copy of *df* with added column 'd_spacing' (Å).
        """
        if "two_theta" not in df.columns:
            raise ValueError("DataFrame must contain a 'two_theta' column.")
        df = df.copy()
        df["d_spacing"] = self.from_two_theta_array(df["two_theta"].to_numpy())
        logger.debug("Computed d-spacings for %d rows.", len(df))
        return df

    # ------------------------------------------------------------------
    # Comparison utility
    # ------------------------------------------------------------------

    def compare_to_standard(
        self,
        experimental_d: list[float],
        standard_d: list[float],
        tolerance_A: float = 0.05,
    ) -> dict:
        """
        Compare experimental d-spacings against a standard compound's values.

        Parameters
        ----------
        experimental_d : list[float]
            d-spacings derived from detected peaks.
        standard_d : list[float]
            Reference d-spacings from the compound database.
        tolerance_A : float
            Maximum |d_exp − d_std| for a match (Å). Default 0.05 Å.

        Returns
        -------
        dict
            {
              'matches': list of (d_exp, d_std, delta_d) tuples,
              'match_count': int,
              'match_fraction': float  (0–1)
            }
        """
        matches = []
        for d_std in standard_d:
            for d_exp in experimental_d:
                if abs(d_exp - d_std) <= tolerance_A:
                    matches.append((round(d_exp, 4), round(d_std, 4), round(abs(d_exp - d_std), 4)))
                    break

        return {
            "matches": matches,
            "match_count": len(matches),
            "match_fraction": len(matches) / len(standard_d) if standard_d else 0.0,
        }