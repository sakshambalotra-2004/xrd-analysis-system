"""
services/crystal_analyzer.py
=============================
Crystal Analysis Module — Stage 9 of the XRD analysis pipeline.

Computes all crystallographic quantities derived from peak positions and widths:

  1. d-Spacing       — via Bragg's Law:        n λ = 2 d sin θ
  2. Crystallite Size — via Scherrer Equation:  D = K λ / (β cos θ)
  3. Peak Shift       — Δ2θ = 2θ_sample − 2θ_reference
  4. Strain / Stress indicators from systematic peak shifts

All angles are passed/returned in degrees; internal calculations use radians.

Usage:
    from services.crystal_analyzer import CrystalAnalyzer
    from services.peak_matcher import MatchResult

    ca = CrystalAnalyzer()
    analysis = ca.analyze(peaks_df, best_match)
"""

import logging
import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from config import settings
from services.peak_matcher import MatchResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class CrystalAnalysis:
    """All crystallographic quantities for one sample."""

    # Scherrer
    crystallite_size_nm: float = 0.0          # D in nanometres
    crystallite_size_angstrom: float = 0.0    # D in Ångströms

    # Bragg d-spacings for each detected peak
    d_spacings: list[float] = field(default_factory=list)     # Å, same order as peaks_df

    # Peak shift vs matched standard
    peak_shifts_deg: list[float] = field(default_factory=list)  # per matched peak
    mean_peak_shift_deg: float = 0.0                            # average Δ2θ
    strain_indicator: str = "None"                              # Tensile / Compressive / None

    # Multi-phase
    detected_phases: list[str] = field(default_factory=list)

    # Raw data echoed back for report generation
    primary_compound: str = ""
    formula: str = ""
    crystal_system: str = ""
    space_group: str = ""
    polytype: str = ""          # FIX: explicit field so report_generator can read it directly
    confidence_score: float = 0.0


# ---------------------------------------------------------------------------
# Analyser
# ---------------------------------------------------------------------------

class CrystalAnalyzer:
    """
    Computes crystallographic properties from detected peaks and the best
    compound match.

    Parameters
    ----------
    wavelength_A : float
        X-ray wavelength in Ångströms (default Cu Kα = 1.5406 Å).
    scherrer_k : float
        Scherrer shape factor K (default 0.9).
    bragg_n : int
        Diffraction order n (default 1).
    """

    def __init__(
        self,
        wavelength_A: float | None = None,
        scherrer_k: float | None = None,
        bragg_n: int | None = None,
    ) -> None:
        self.lam = wavelength_A or settings.WAVELENGTH_ANGSTROM  # Å
        self.K = scherrer_k or settings.SCHERRER_K
        self.n = bragg_n or settings.BRAGG_ORDER

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(
        self,
        peaks_df: pd.DataFrame,
        best_match: MatchResult | None,
        all_matches: list[MatchResult] | None = None,
    ) -> CrystalAnalysis:
        """
        Run the full crystallographic analysis for one sample.

        Parameters
        ----------
        peaks_df : pd.DataFrame
            Output of PeakDetector (columns: two_theta, intensity, fwhm_deg).
        best_match : MatchResult | None
            Top compound match from PeakMatcher.
        all_matches : list[MatchResult] | None
            Full candidate list for multi-phase detection.

        Returns
        -------
        CrystalAnalysis
        """
        result = CrystalAnalysis()

        if peaks_df.empty:
            logger.warning("Empty peaks_df in CrystalAnalyzer.analyze — returning defaults.")
            # Explicit default fallback to prevent empty labels on frontend
            result.primary_compound = "No Crystalline Match Found"
            result.crystal_system = "Disordered / Amorphous"
            result.detected_phases = ["Amorphous Background Matrix"]
            return result

        # ---- 1. d-Spacings (Bragg's Law) ----
        result.d_spacings = self._compute_d_spacings(peaks_df["two_theta"].to_numpy())

        # ---- 2. Crystallite size (Scherrer) ----
        if "fwhm_deg" in peaks_df.columns:
            size_A = self._scherrer_average(
                peaks_df["two_theta"].to_numpy(),
                peaks_df["fwhm_deg"].to_numpy(),
            )
            result.crystallite_size_angstrom = round(size_A, 2)
            result.crystallite_size_nm = round(size_A / 10.0, 2)

        # ---- 3. Structural Information Processing ----
        if best_match:
            shifts = [mp.delta_two_theta for mp in best_match.matched_peaks]
            # Preserve sign: positive = sample shifted to higher 2θ
            signed_shifts = [
                mp.two_theta_exp - mp.two_theta_std
                for mp in best_match.matched_peaks
            ]
            result.peak_shifts_deg = [round(s, 4) for s in signed_shifts]
            result.mean_peak_shift_deg = round(float(np.mean(signed_shifts)), 4) if signed_shifts else 0.0
            result.strain_indicator = self._strain_indicator(result.mean_peak_shift_deg)

            # FIX: store polytype as a standalone field so downstream consumers
            # (report_generator, API response) don't have to parse it out of the
            # primary_compound string.
            polytype_val = getattr(best_match, "polytype", "")
            result.polytype = polytype_val

            # Keep the human-readable compound name clean — only append polytype
            # suffix when it isn't already embedded in compound_name.
            polytype_suffix = f" ({polytype_val})" if polytype_val and polytype_val not in best_match.compound_name else ""
            result.primary_compound = f"{best_match.compound_name}{polytype_suffix}"
            result.formula = best_match.formula
            result.crystal_system = best_match.crystal_system
            result.space_group = best_match.space_group
            result.confidence_score = best_match.similarity_score
        else:
            # Amorphous protective fallback mode
            result.primary_compound = "No Crystalline Match Found"
            result.formula = "N/A"
            result.crystal_system = "Disordered / Amorphous"
            result.space_group = "N/A"
            result.confidence_score = 0.0

        # ---- 4. Multi-phase detection ----
        if all_matches and best_match:
            result.detected_phases = []
            for m in all_matches:
                if m.similarity_score >= settings.MIN_SIMILARITY_SCORE:
                    # UPGRADE: Stitch polytypes directly into formula string list cards (e.g. "SiC (3C)")
                    p_val = getattr(m, "polytype", "")
                    p_suffix = f" ({p_val})" if p_val else ""
                    result.detected_phases.append(f"{m.formula}{p_suffix}")
        else:
            result.detected_phases = ["Amorphous Background Matrix"]

        logger.info(
            "Analysis complete — D=%.1f nm, Δ2θ=%.4f°, strain=%s, phases=%s",
            result.crystallite_size_nm,
            result.mean_peak_shift_deg,
            result.strain_indicator,
            result.detected_phases,
        )
        return result

    # ------------------------------------------------------------------
    # Crystallographic calculations
    # ------------------------------------------------------------------

    def d_spacing(self, two_theta_deg: float) -> float:
        """
        Bragg's Law: d = n λ / (2 sin θ).

        Parameters
        ----------
        two_theta_deg : float
            Measured 2θ angle in degrees.

        Returns
        -------
        float
            d-spacing in Ångströms.
        """
        theta_rad = math.radians(two_theta_deg / 2.0)
        sin_theta = math.sin(theta_rad)
        if sin_theta == 0:
            return 0.0
        return round((self.n * self.lam) / (2.0 * sin_theta), 4)

    def crystallite_size(self, two_theta_deg: float, fwhm_deg: float) -> float:
        """
        Scherrer Equation: D = K λ / (beta * cos θ).

        Parameters
        ----------
        two_theta_deg : float
            Peak centre in degrees.
        fwhm_deg : float
            Full-width at half maximum in degrees.

        Returns
        -------
        float
            Crystallite size D in Ångströms.
        """
        if fwhm_deg <= 0:
            return 0.0
        theta_rad = math.radians(two_theta_deg / 2.0)
        beta_rad = math.radians(fwhm_deg)
        if beta_rad == 0 or math.cos(theta_rad) == 0:
            return 0.0
        return round((self.K * self.lam) / (beta_rad * math.cos(theta_rad)), 2)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_d_spacings(self, two_theta_array: np.ndarray) -> list[float]:
        return [self.d_spacing(float(t)) for t in two_theta_array]

    def _scherrer_average(self, two_theta: np.ndarray, fwhm: np.ndarray) -> float:
        """Average crystallite size over all peaks with valid FWHM."""
        sizes = []
        for t, b in zip(two_theta, fwhm):
            if b > 0:
                sizes.append(self.crystallite_size(float(t), float(b)))
        if not sizes:
            return 0.0
        # Weight by 1/FWHM (sharper peaks give more reliable estimates)
        weights = 1.0 / np.array([b for b in fwhm if b > 0])
        return float(np.average(sizes, weights=weights))

    @staticmethod
    def _strain_indicator(mean_shift: float) -> str:
        """Classify peak shift direction as strain indicator."""
        if abs(mean_shift) < 0.05:
            return "None"
        return "Compressive" if mean_shift < 0 else "Tensile"