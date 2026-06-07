"""
services/similarity_engine.py
==============================
Similarity Scoring Module — Stage 5 of the XRD analysis pipeline.

Extends basic peak-count similarity with weighted scoring strategies that
factor in:
  - Intensity matching      (peaks with closer relative intensity score higher)
  - d-spacing deviation     (smaller Δd contributes more weight)
  - Peak count bonus        (more matched peaks → higher confidence)

All scores are normalised to 0–100.

Usage:
    from services.similarity_engine import SimilarityEngine
    from services.peak_matcher import MatchResult

    engine = SimilarityEngine()
    score = engine.weighted_score(match_result)
    ranked = engine.rank_candidates(candidates)   # list[MatchResult]
"""

import logging
import math
from typing import Sequence

import numpy as np

from config import settings
from services.peak_matcher import MatchResult, MatchedPeak

logger = logging.getLogger(__name__)


class SimilarityEngine:
    """
    Computes weighted similarity scores for candidate MatchResults and
    re-ranks them.

    Parameters
    ----------
    w_count : float
        Weight given to the fraction of standard peaks matched. Default 0.5.
    w_intensity : float
        Weight given to intensity similarity. Default 0.3.
    w_d_spacing : float
        Weight given to d-spacing closeness. Default 0.2.
    """

    def __init__(
        self,
        w_count: float = 0.50,
        w_intensity: float = 0.30,
        w_d_spacing: float = 0.20,
    ) -> None:
        total = w_count + w_intensity + w_d_spacing
        if not math.isclose(total, 1.0, abs_tol=1e-6):
            raise ValueError(f"Weights must sum to 1.0 (got {total:.4f}).")
        self.w_count = w_count
        self.w_intensity = w_intensity
        self.w_d_spacing = w_d_spacing

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def weighted_score(self, result: MatchResult) -> float:
        """
        Compute a weighted similarity score for one MatchResult.

        Returns
        -------
        float
            Score in [0, 100].
        """
        if result.total_standard_peaks == 0:
            return 0.0

        count_score = self._count_score(result)
        intensity_score = self._intensity_score(result.matched_peaks)
        d_score = self._d_spacing_score(result.matched_peaks)

        weighted = (
            self.w_count     * count_score
            + self.w_intensity * intensity_score
            + self.w_d_spacing * d_score
        )
        return round(min(weighted * 100.0, 100.0), 2)

    def rank_candidates(self, candidates: Sequence[MatchResult]) -> list[MatchResult]:
        """
        Re-rank candidates using the weighted score and return sorted list
        (highest score first).

        The ``similarity_score`` attribute on each MatchResult is updated
        in-place with the weighted value.
        """
        for c in candidates:
            c.similarity_score = self.weighted_score(c)
        ranked = sorted(candidates, key=lambda r: r.similarity_score, reverse=True)
        if ranked:
            logger.info(
                "Weighted ranking — top: %s (%.1f%%)",
                ranked[0].compound_name,
                ranked[0].similarity_score,
            )
        return ranked

    # ------------------------------------------------------------------
    # Component scores (all return values in [0, 1])
    # ------------------------------------------------------------------

    def _count_score(self, result: MatchResult) -> float:
        """Fraction of standard peaks that were matched."""
        return result.matched_count / result.total_standard_peaks

    def _intensity_score(self, matched: list[MatchedPeak]) -> float:
        """
        Average normalised intensity agreement across matched peaks.
        Score = 1 − mean(|I_exp_norm − I_std_norm|).
        """
        if not matched:
            return 0.0

        max_exp = max(mp.intensity_exp for mp in matched) or 1.0
        max_std = max(mp.intensity_std for mp in matched) or 1.0

        diffs = []
        for mp in matched:
            norm_exp = mp.intensity_exp / max_exp
            norm_std = mp.intensity_std / max_std
            diffs.append(abs(norm_exp - norm_std))

        return max(0.0, 1.0 - float(np.mean(diffs)))

    def _d_spacing_score(self, matched: list[MatchedPeak]) -> float:
        """
        Score based on how close measured d-spacings are to reference.
        Uses a Gaussian decay: score = exp(−(Δd / σ)²), σ = 0.05 Å.
        """
        if not matched:
            return 0.0

        sigma = 0.05  # Å
        scores = []
        for mp in matched:
            if mp.d_spacing == 0:
                continue
            # Recalculate experimental d from 2θ_exp using Bragg's Law
            # FIX: use settings.WAVELENGTH_ANGSTROM instead of hardcoded 1.5406
            # so the score is consistent when a non-Cu-Kα source is configured.
            lam = settings.WAVELENGTH_ANGSTROM
            theta_exp = math.radians(mp.two_theta_exp / 2.0)
            d_exp = lam / (2.0 * math.sin(theta_exp)) if math.sin(theta_exp) > 0 else 0
            delta_d = abs(d_exp - mp.d_spacing)
            scores.append(math.exp(-(delta_d / sigma) ** 2))

        return float(np.mean(scores)) if scores else 0.0