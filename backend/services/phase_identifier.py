"""
services/phase_identifier.py
=============================
Phase Identification Module — Stage 6 of the XRD analysis pipeline.

Determines the primary compound and detects secondary phases from the ranked
list of MatchResult candidates. Uses an iterative residual matching strategy.

FIX SUMMARY
-----------
1. Residual angle matching now uses a tolerance-based comparison (±0.01°)
   instead of exact float set membership — prevents rounding differences between
   matched_peaks.two_theta_exp and peaks_df.two_theta from mis-classifying
   explained peaks as residual and generating spurious secondary phases.

2. Duplicate-phase guard now includes polytype in the comparison key, so
   different polytypes of the same compound (e.g. SiC 6H vs SiC 4H) are
   correctly accepted as distinct secondary phases rather than being blocked.
"""

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from config import settings
from services.peak_matcher import MatchResult, PeakMatcher

logger = logging.getLogger(__name__)

SECONDARY_SCORE_THRESHOLD = 30.0

# Tolerance for matching two_theta_exp values between matched_peaks and peaks_df
# Must be tighter than the peak-matching tolerance (0.2°) but forgiving of
# float rounding differences between pipeline stages.
_ANGLE_TOLERANCE_DEG = 0.01


def _is_explained(angle: float, explained: list[float], tol: float = _ANGLE_TOLERANCE_DEG) -> bool:
    """Return True if *angle* is within *tol* of any angle in *explained*."""
    return any(abs(angle - e) <= tol for e in explained)


@dataclass
class PhaseIdentificationResult:
    """Result of phase identification for one sample."""
    primary: MatchResult | None = None
    secondary: list[MatchResult] = field(default_factory=list)

    @property
    def all_phases(self) -> list[MatchResult]:
        phases = []
        if self.primary:
            phases.append(self.primary)
        phases.extend(self.secondary)
        return phases

    @property
    def phase_formulas(self) -> list[str]:
        """
        Returns formulas annotated with crystal system to differentiate
        polymorphs (e.g. 'SiC (Cubic)', 'SiC (Hexagonal)').
        """
        formulas = []
        for p in self.all_phases:
            crystal_sys = getattr(p, "crystal_system", None)
            if crystal_sys:
                formulas.append(f"{p.formula} ({crystal_sys})")
            else:
                formulas.append(p.formula)
        return formulas

    @property
    def is_multiphase(self) -> bool:
        return len(self.secondary) > 0


class PhaseIdentifier:
    """
    Identifies primary and secondary crystalline phases from candidate matches.

    Parameters
    ----------
    secondary_score_threshold : float
        Minimum weighted score for a secondary phase to be accepted on residual data.
    """

    def __init__(
        self,
        secondary_score_threshold: float = SECONDARY_SCORE_THRESHOLD,
    ) -> None:
        self.secondary_threshold = secondary_score_threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def identify(
        self,
        candidates: list[MatchResult],
        peaks_df: pd.DataFrame,
    ) -> PhaseIdentificationResult:
        """
        Identify primary and secondary phases using iterative residual matching.

        Parameters
        ----------
        candidates : list[MatchResult]
            Ranked output from PeakMatcher (highest score first).
        peaks_df : pd.DataFrame
            Detected experimental peaks (two_theta, intensity).

        Returns
        -------
        PhaseIdentificationResult
        """
        result = PhaseIdentificationResult()

        if not candidates:
            logger.warning("PhaseIdentifier: no candidates supplied.")
            return result

        # Pass 1 — Extract the dominant Primary Phase
        result.primary = candidates[0]
        logger.info(
            "Primary phase identified: %s  polytype=%s  score=%.1f%%",
            result.primary.compound_name,
            getattr(result.primary, "polytype", "?"),
            result.primary.similarity_score,
        )

        if peaks_df.empty:
            return result

        # Pass 2 — Isolate unexplained peaks to catch secondary/trace phases
        # FIX: use tolerance-based comparison instead of exact float set membership
        # to avoid rounding differences between matched_peaks and peaks_df causing
        # valid explained peaks to be misclassified as residual.
        explained_angles = [mp.two_theta_exp for mp in result.primary.matched_peaks]
        all_angles = peaks_df["two_theta"].tolist()

        residual_angles = [
            a for a in all_angles
            if not _is_explained(a, explained_angles)
        ]

        if not residual_angles:
            logger.info("All experimental peaks are fully explained by the primary phase.")
            return result

        logger.info(
            "%d unexplained peak(s) after primary phase. Searching for secondary phases…",
            len(residual_angles),
        )

        residual_df = peaks_df[peaks_df["two_theta"].isin(residual_angles)].copy()

        matcher = PeakMatcher()
        residual_candidates = matcher.match(residual_df, max_candidates=5)

        if not residual_candidates:
            logger.info("No database standards matched the residual peaks.")
            return result

        # FIX: duplicate key now includes polytype so that different polytypes of
        # the same compound (6H vs 4H, cubic vs hexagonal SiC) are NOT blocked.
        primary_key = (
            result.primary.compound_name,
            getattr(result.primary, "crystal_system", ""),
            getattr(result.primary, "polytype", ""),
        )

        for sub_candidate in residual_candidates:
            candidate_key = (
                sub_candidate.compound_name,
                getattr(sub_candidate, "crystal_system", ""),
                getattr(sub_candidate, "polytype", ""),
            )

            if candidate_key == primary_key:
                logger.debug("Skipping duplicate of primary: %s", candidate_key)
                continue

            if sub_candidate.similarity_score >= self.secondary_threshold:
                result.secondary.append(sub_candidate)
                logger.info(
                    "Secondary phase accepted: %s  polytype=%s  crystal_system=%s  score=%.1f%%",
                    sub_candidate.compound_name,
                    getattr(sub_candidate, "polytype", "?"),
                    getattr(sub_candidate, "crystal_system", "?"),
                    sub_candidate.similarity_score,
                )
            else:
                logger.debug(
                    "Secondary candidate rejected (score %.1f%% < threshold %.1f%%): %s",
                    sub_candidate.similarity_score,
                    self.secondary_threshold,
                    sub_candidate.compound_name,
                )

        return result