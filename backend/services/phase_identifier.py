"""
services/phase_identifier.py
=============================
Phase Identification Module — Stage 6 of the XRD analysis pipeline.

Determines the primary compound and detects secondary phases from the ranked
list of MatchResult candidates.  Uses a two-pass strategy:

  Pass 1 — Primary phase
      The highest-scoring candidate above MIN_SIMILARITY_SCORE is the
      primary compound.

  Pass 2 — Secondary phases (multi-phase detection)
      Experimental peaks not explained by the primary phase are matched
      against remaining candidates.  Any candidate whose unmatched-peak
      score exceeds SECONDARY_SCORE_THRESHOLD is added as a secondary phase.

Usage:
    from services.phase_identifier import PhaseIdentifier

    identifier = PhaseIdentifier()
    result = identifier.identify(candidates, peaks_df)
    print(result.primary.compound_name)
    print([s.compound_name for s in result.secondary])
"""

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from config import settings
from services.peak_matcher import MatchResult, PeakMatcher

logger = logging.getLogger(__name__)

# Minimum score for a compound to be declared a secondary phase
SECONDARY_SCORE_THRESHOLD = 30.0

# Minimum fraction of experimental peaks that must be "unexplained" before
# searching for a secondary phase
RESIDUAL_PEAK_FRACTION = 0.25


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
        return [p.formula for p in self.all_phases]

    @property
    def is_multiphase(self) -> bool:
        return len(self.secondary) > 0


class PhaseIdentifier:
    """
    Identifies primary and secondary crystalline phases from candidate matches.

    Parameters
    ----------
    secondary_score_threshold : float
        Minimum weighted score for a secondary phase to be accepted.
    residual_peak_fraction : float
        Minimum fraction of unexplained peaks before secondary search runs.
    """

    def __init__(
        self,
        secondary_score_threshold: float = SECONDARY_SCORE_THRESHOLD,
        residual_peak_fraction: float = RESIDUAL_PEAK_FRACTION,
    ) -> None:
        self.secondary_threshold = secondary_score_threshold
        self.residual_fraction = residual_peak_fraction

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def identify(
        self,
        candidates: list[MatchResult],
        peaks_df: pd.DataFrame,
    ) -> PhaseIdentificationResult:
        """
        Identify primary and secondary phases.

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

        # Pass 1 — Primary phase
        result.primary = candidates[0]
        logger.info(
            "Primary phase: %s (%.1f%%)",
            result.primary.compound_name,
            result.primary.similarity_score,
        )

        if peaks_df.empty or len(candidates) < 2:
            return result

        # Pass 2 — Check for secondary phases via residual peaks
        explained_angles = {mp.two_theta_exp for mp in result.primary.matched_peaks}
        all_angles = set(peaks_df["two_theta"].tolist())
        residual_angles = all_angles - explained_angles
        residual_fraction = len(residual_angles) / len(all_angles) if all_angles else 0.0

        if residual_fraction < self.residual_fraction:
            logger.info(
                "Residual peak fraction %.1f%% — no secondary phase search needed.",
                residual_fraction * 100,
            )
            return result

        logger.info(
            "%.1f%% unexplained peaks — searching for secondary phases.",
            residual_fraction * 100,
        )

        residual_df = peaks_df[peaks_df["two_theta"].isin(residual_angles)].copy()

        for candidate in candidates[1:]:
            if candidate.similarity_score < self.secondary_threshold:
                continue
            # Re-match only residual peaks
            matcher = PeakMatcher()
            sub_candidates = matcher.match(residual_df, max_candidates=1)
            if sub_candidates and sub_candidates[0].compound_name == candidate.compound_name:
                result.secondary.append(candidate)
                logger.info("Secondary phase detected: %s", candidate.compound_name)
                # Remove peaks now explained by this secondary phase
                newly_explained = {mp.two_theta_exp for mp in sub_candidates[0].matched_peaks}
                residual_df = residual_df[~residual_df["two_theta"].isin(newly_explained)]
                if residual_df.empty:
                    break

        return result