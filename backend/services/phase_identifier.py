"""
services/phase_identifier.py
=============================
Phase Identification Module — Stage 6 of the XRD analysis pipeline.

Determines the primary compound and detects secondary phases from the ranked
list of MatchResult candidates. Uses an iterative residual matching strategy.
"""

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from config import settings
from services.peak_matcher import MatchResult, PeakMatcher

logger = logging.getLogger(__name__)

# Minimum score a compound must achieve on the residual data to be accepted as a secondary phase
SECONDARY_SCORE_THRESHOLD = 30.0


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
        Returns a list of formulas annotated with their crystal systems 
        to differentiate polymorphs (e.g., 'SiC (Cubic)', 'SiC (Hexagonal)').
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
            "Primary phase identified: %s (%.1f%%)",
            result.primary.compound_name,
            result.primary.similarity_score,
        )

        if peaks_df.empty:
            return result

        # Pass 2 — Isolate unexplained peaks to catch secondary/trace phases
        explained_angles = {mp.two_theta_exp for mp in result.primary.matched_peaks}
        all_angles = set(peaks_df["two_theta"].tolist())
        residual_angles = all_angles - explained_angles

        # If there are no remaining unmatched peaks, exit early
        if not residual_angles:
            logger.info("All experimental peaks are fully explained by the primary phase.")
            return result

        logger.info(
            "Found %d unexplained peak(s). Searching for secondary phases...",
            len(residual_angles),
        )

        # Filter down the dataframe to only contain the residual peak data
        residual_df = peaks_df[peaks_df["two_theta"].isin(residual_angles)].copy()

        # Run the matcher directly on the remaining peak dataset
        matcher = PeakMatcher()
        residual_candidates = matcher.match(residual_df, max_candidates=5)

        if not residual_candidates:
            logger.info("No matching database standards found for the residual peaks.")
            return result

        for sub_candidate in residual_candidates:
            # FIXED: Guard check now checks both name AND crystal system.
            # This allows different polymorphs of Silicon Carbide (Cubic vs Hexagonal) to be added!
            is_duplicate_of_primary = (
                sub_candidate.compound_name == result.primary.compound_name and
                getattr(sub_candidate, "crystal_system", "") == getattr(result.primary, "crystal_system", "")
            )
            
            if is_duplicate_of_primary:
                continue

            # Evaluate the confidence score based purely on the residual match quality
            if sub_candidate.similarity_score >= self.secondary_threshold:
                result.secondary.append(sub_candidate)
                logger.info(
                    "Secondary phase detected: %s - %s (Residual Match Score: %.1f%%)",
                    sub_candidate.compound_name,
                    getattr(sub_candidate, "crystal_system", "Unknown"),
                    sub_candidate.similarity_score,
                )

        return result