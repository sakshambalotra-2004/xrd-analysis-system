"""
services/peak_matcher.py
========================
Peak Matching Engine — Stage 4 of the XRD analysis pipeline.

Compares detected experimental peaks against every standard compound in the
JSON database and returns a ranked list of candidate matches using an advanced
Figure of Merit (FOM) alignment scoring framework.

Upgraded to ensure structural polytype variants are tracked across peak intersections.
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
    phase_name: str = ""
    polytype: str = ""  # UPGRADE: Track polytype per individual peak row


@dataclass
class MatchResult:
    """Full match result for one standard compound."""
    compound_name: str
    formula: str
    crystal_system: str
    space_group: str
    similarity_score: float
    matched_peaks: list[MatchedPeak] = field(default_factory=list)
    polytype: str = ""  # UPGRADE: Track polytype for the overall standard match
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
                "Top match: %s %s (%.1f%% confidence, %d/%d peaks matched)",
                top[0].compound_name,
                f"[{top[0].polytype}]" if top[0].polytype else "",
                top[0].similarity_score,
                top[0].matched_count,
                top[0].total_standard_peaks,
            )

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
        for fpath in files:
            try:
                with open(fpath, encoding="utf-8") as f:
                    data = json.load(f)
                    self._standards.append(data)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Skipping %s — %s", fpath.name, exc)

    def _match_one(
        self,
        std: dict,
        exp_angles: np.ndarray,
        exp_intensities: np.ndarray,
        n_exp: int,
    ) -> MatchResult:
        """Compare one standard compound against experimental peaks."""
        compound_name = std.get("compound_name", "Unknown")
        polytype = str(std.get("polytype", ""))  # UPGRADE: Extract polytype from JSON standard
        std_peaks = std.get("peaks", [])
        matched: list[MatchedPeak] = []
        matched_std_angles = set()
        matched_exp_indices = set()  # FIX: prevent one exp peak matching multiple std peaks

        for sp in std_peaks:
            std_angle = float(sp["two_theta"])
            deltas = np.abs(exp_angles - std_angle)
            closest_idx = int(np.argmin(deltas))

            # FIX: skip if this experimental peak was already consumed by a closer std peak
            if closest_idx in matched_exp_indices:
                # Try the next-closest that hasn't been used yet
                sorted_idxs = np.argsort(deltas)
                closest_idx = next(
                    (i for i in sorted_idxs if i not in matched_exp_indices),
                    None,
                )
                if closest_idx is None:
                    continue

            if deltas[closest_idx] <= self.tolerance:
                matched.append(MatchedPeak(
                    two_theta_exp=float(exp_angles[closest_idx]),
                    two_theta_std=std_angle,
                    delta_two_theta=float(exp_angles[closest_idx] - std_angle),
                    intensity_exp=float(exp_intensities[closest_idx]),
                    intensity_std=float(sp.get("intensity", 0)),
                    d_spacing=float(sp.get("d", 0)),
                    h=int(sp.get("h", 0)),
                    k=int(sp.get("k", 0)),
                    l=int(sp.get("l", 0)),
                    phase_name=compound_name,
                    polytype=polytype,
                ))
                matched_std_angles.add(std_angle)
                matched_exp_indices.add(closest_idx)  # FIX: mark as consumed

        n_std = len(std_peaks)
        n_matched = len(matched_std_angles)

        
        # Replace your existing _match_one score calculation with this:
        score = 0.0
        if n_std > 0 and n_matched > 0:
            coverage_ratio = n_matched / n_std
            
            # REWARD COMPLEXITY: Higher score for matching more absolute peaks
            absolute_match_bonus = min(n_matched / 12.0, 1.0) 
            
            mean_angular_error = np.mean([abs(m.delta_two_theta) for m in matched])
            accuracy_ratio = max(0.0, 1.0 - (mean_angular_error / self.tolerance))
            
            # Weighted formula: 30% coverage, 40% complexity bonus, 30% accuracy
            score = (coverage_ratio * 30.0) + (absolute_match_bonus * 40.0) + (accuracy_ratio * 30.0)

        return MatchResult(
            compound_name=compound_name,
            formula=std.get("formula", "?"),
            crystal_system=std.get("crystal_system", "Unknown"),
            space_group=std.get("space_group", "Unknown"),
            similarity_score=round(score, 2),
            matched_peaks=matched,
            polytype=polytype, # UPGRADE: Attach polytype to the overall match result
            total_standard_peaks=n_std,
            total_experimental_peaks=n_exp,
        )