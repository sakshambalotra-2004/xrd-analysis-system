"""
services/peak_matcher.py
========================
Peak Matching Engine — Stage 4 of the XRD analysis pipeline.

Compares detected experimental peaks against every standard compound in the
JSON database and returns a ranked list of candidate matches.

Matching Condition
------------------
A peak is considered matched when:

    |2θ_exp − 2θ_std| ≤ PEAK_MATCH_TOLERANCE_DEG   (default 0.2°)

Similarity Score
----------------
    Score = (Matched Peaks / Total Standard Peaks) × 100

Usage:
    from services.peak_matcher import PeakMatcher

    matcher = PeakMatcher()
    candidates = matcher.match(peaks_df)
    # candidates: list of MatchResult sorted by score descending
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class MatchedPeak:
    """A single peak that was matched between experiment and standard."""
    two_theta_exp: float
    two_theta_std: float
    delta_two_theta: float
    intensity_exp: float
    intensity_std: float
    d_spacing: float
    h: int
    k: int
    l: int


@dataclass
class MatchResult:
    """Full match result for one standard compound."""
    compound_name: str
    formula: str
    crystal_system: str
    space_group: str
    similarity_score: float          # 0–100 %
    matched_peaks: list[MatchedPeak] = field(default_factory=list)
    total_standard_peaks: int = 0
    total_experimental_peaks: int = 0

    @property
    def matched_count(self) -> int:
        return len(self.matched_peaks)


# ---------------------------------------------------------------------------
# Matcher
# ---------------------------------------------------------------------------

class PeakMatcher:
    """
    Matches experimental XRD peaks against the standards database.

    Parameters
    ----------
    standards_dir : str | Path | None
        Directory containing the compound JSON files.  Defaults to
        ``settings.STANDARDS_DIR``.
    tolerance_deg : float
        Maximum |2θ_exp − 2θ_std| for a match.  Defaults to
        ``settings.PEAK_MATCH_TOLERANCE_DEG``.
    """

    def __init__(
        self,
        standards_dir: str | Path | None = None,
        tolerance_deg: float | None = None,
    ) -> None:
        self.standards_dir = Path(standards_dir or settings.STANDARDS_DIR)
        self.tolerance = tolerance_deg or settings.PEAK_MATCH_TOLERANCE_DEG
        self._standards: list[dict] = []
        self._load_standards()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def match(
        self,
        peaks_df: pd.DataFrame,
        max_candidates: int | None = None,
    ) -> list[MatchResult]:
        """
        Match experimental peaks against all loaded standards.

        Parameters
        ----------
        peaks_df : pd.DataFrame
            Output of PeakDetector.detect().  Must contain 'two_theta' column.
        max_candidates : int | None
            Return at most this many candidates (sorted by score descending).
            Defaults to ``settings.MAX_CANDIDATES``.

        Returns
        -------
        list[MatchResult]
            Candidates above ``settings.MIN_SIMILARITY_SCORE``, sorted by
            similarity_score descending.
        """
        if peaks_df.empty:
            logger.warning("Empty peaks_df passed to PeakMatcher.")
            return []

        exp_angles = peaks_df["two_theta"].to_numpy()
        exp_intensities = peaks_df["intensity"].to_numpy()
        max_cand = max_candidates or settings.MAX_CANDIDATES
        results: list[MatchResult] = []

        for std in self._standards:
            result = self._match_one(std, exp_angles, exp_intensities, len(exp_angles))
            if result.similarity_score >= settings.MIN_SIMILARITY_SCORE:
                results.append(result)

        results.sort(key=lambda r: r.similarity_score, reverse=True)
        top = results[:max_cand]

        if top:
            logger.info(
                "Top match: %s (%.1f%% confidence, %d/%d peaks matched)",
                top[0].compound_name,
                top[0].similarity_score,
                top[0].matched_count,
                top[0].total_standard_peaks,
            )
        else:
            logger.warning("No compound matched above the minimum score threshold.")

        return top

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_standards(self) -> None:
        """Load all JSON standard files from the standards directory."""
        if not self.standards_dir.exists():
            logger.error("Standards directory not found: %s", self.standards_dir)
            return

        files = list(self.standards_dir.glob("*.json"))
        logger.info("Loading %d standard compound files from %s", len(files), self.standards_dir)

        for fpath in files:
            try:
                with open(fpath, encoding="utf-8") as f:
                    data = json.load(f)
                self._standards.append(data)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Skipping %s — %s", fpath.name, exc)

        logger.info("Loaded %d standard compounds.", len(self._standards))

    def _match_one(
        self,
        std: dict,
        exp_angles: np.ndarray,
        exp_intensities: np.ndarray,
        n_exp: int,
    ) -> MatchResult:
        """Compare one standard compound against experimental peaks."""
        std_peaks = std.get("peaks", [])
        matched: list[MatchedPeak] = []

        for sp in std_peaks:
            std_angle = float(sp["two_theta"])
            deltas = np.abs(exp_angles - std_angle)
            closest_idx = int(np.argmin(deltas))

            if deltas[closest_idx] <= self.tolerance:
                matched.append(MatchedPeak(
                    two_theta_exp=float(exp_angles[closest_idx]),
                    two_theta_std=std_angle,
                    delta_two_theta=float(deltas[closest_idx]),
                    intensity_exp=float(exp_intensities[closest_idx]),
                    intensity_std=float(sp.get("intensity", 0)),
                    d_spacing=float(sp.get("d", 0)),
                    h=int(sp.get("h", 0)),
                    k=int(sp.get("k", 0)),
                    l=int(sp.get("l", 0)),
                ))

        n_std = len(std_peaks)
        score = (len(matched) / n_std * 100) if n_std > 0 else 0.0

        return MatchResult(
            compound_name=std.get("compound_name", "Unknown"),
            formula=std.get("formula", "?"),
            crystal_system=std.get("crystal_system", "Unknown"),
            space_group=std.get("space_group", "Unknown"),
            similarity_score=round(score, 2),
            matched_peaks=matched,
            total_standard_peaks=n_std,
            total_experimental_peaks=n_exp,
        )