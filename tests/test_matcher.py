"""
tests/test_matcher.py
======================
Unit tests for services/peak_matcher.py — Peak Matching Engine.
"""

import json
import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from services.peak_matcher import MatchResult, PeakMatcher


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SIC_STANDARD = {
    "compound_name": "Silicon Carbide",
    "formula": "SiC",
    "crystal_system": "Hexagonal",
    "space_group": "P63mc",
    "peaks": [
        {"two_theta": 35.60, "d": 2.52, "intensity": 100, "h": 1, "k": 0, "l": 1},
        {"two_theta": 41.40, "d": 2.17, "intensity": 60,  "h": 1, "k": 0, "l": 2},
        {"two_theta": 60.00, "d": 1.54, "intensity": 45,  "h": 1, "k": 1, "l": 1},
        {"two_theta": 71.80, "d": 1.32, "intensity": 30,  "h": 2, "k": 0, "l": 0},
    ],
}

SIO2_STANDARD = {
    "compound_name": "Silicon Dioxide",
    "formula": "SiO2",
    "crystal_system": "Trigonal",
    "space_group": "P3221",
    "peaks": [
        {"two_theta": 20.85, "d": 4.26, "intensity": 35,  "h": 1, "k": 0, "l": 0},
        {"two_theta": 26.64, "d": 3.34, "intensity": 100, "h": 1, "k": 0, "l": 1},
        {"two_theta": 50.12, "d": 1.82, "intensity": 13,  "h": 1, "k": 1, "l": 2},
    ],
}


@pytest.fixture
def standards_dir(tmp_path):
    """Write standard compound JSON files to a temp directory."""
    for std in [SIC_STANDARD, SIO2_STANDARD]:
        fname = std["formula"].replace(" ", "_").lower() + ".json"
        (tmp_path / fname).write_text(json.dumps(std), encoding="utf-8")
    return str(tmp_path)


@pytest.fixture
def matcher(standards_dir):
    return PeakMatcher(standards_dir=standards_dir, tolerance_deg=0.2)


def _peaks_df(two_theta_list: list[float], intensity_list: list[float] | None = None) -> pd.DataFrame:
    if intensity_list is None:
        intensity_list = [100.0] * len(two_theta_list)
    return pd.DataFrame({"two_theta": two_theta_list, "intensity": intensity_list})


# ---------------------------------------------------------------------------
# Matching tests
# ---------------------------------------------------------------------------

class TestPeakMatcherLoading:
    def test_loads_standards(self, matcher):
        assert len(matcher._standards) == 2

    def test_handles_missing_dir_gracefully(self):
        m = PeakMatcher(standards_dir="/nonexistent/path")
        assert len(m._standards) == 0


class TestMatchingLogic:
    def test_perfect_sic_match(self, matcher):
        """Exact SiC peaks should yield 100% confidence."""
        peaks = _peaks_df([35.60, 41.40, 60.00, 71.80])
        results = matcher.match(peaks)
        assert len(results) > 0
        top = results[0]
        assert top.formula == "SiC"
        assert top.similarity_score == pytest.approx(100.0, abs=0.1)

    def test_tolerance_boundary_exact(self, matcher):
        """Peaks at exactly ±0.2° should still match."""
        peaks = _peaks_df([35.40, 41.20, 59.80, 71.60])  # all shifted -0.2°
        results = matcher.match(peaks)
        sic = next((r for r in results if r.formula == "SiC"), None)
        assert sic is not None
        assert sic.matched_count == 4

    def test_beyond_tolerance_no_match(self, matcher):
        """Peaks shifted more than tolerance should not match."""
        peaks = _peaks_df([35.00, 40.90, 59.50, 71.00])  # shifted -0.6°
        results = matcher.match(peaks)
        sic = next((r for r in results if r.formula == "SiC"), None)
        if sic:
            assert sic.matched_count == 0

    def test_empty_peaks_returns_empty(self, matcher):
        peaks = pd.DataFrame(columns=["two_theta", "intensity"])
        results = matcher.match(peaks)
        assert results == []

    def test_results_sorted_by_score(self, matcher):
        """Results must be sorted descending by similarity_score."""
        peaks = _peaks_df([35.60, 41.40, 60.00, 71.80, 26.64])
        results = matcher.match(peaks)
        scores = [r.similarity_score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_max_candidates_respected(self, matcher):
        peaks = _peaks_df([35.60, 41.40, 60.00, 71.80, 26.64])
        results = matcher.match(peaks, max_candidates=1)
        assert len(results) <= 1


class TestMatchResult:
    def test_matched_count_property(self, matcher):
        peaks = _peaks_df([35.60, 41.40])
        results = matcher.match(peaks)
        sic = next((r for r in results if r.formula == "SiC"), None)
        if sic:
            assert sic.matched_count == len(sic.matched_peaks)

    def test_matched_peak_fields(self, matcher):
        peaks = _peaks_df([35.60], [80.0])
        results = matcher.match(peaks)
        sic = next((r for r in results if r.formula == "SiC"), None)
        if sic and sic.matched_peaks:
            mp = sic.matched_peaks[0]
            assert mp.two_theta_exp == pytest.approx(35.60, abs=0.01)
            assert mp.two_theta_std == pytest.approx(35.60, abs=0.01)
            assert mp.d_spacing > 0
            assert isinstance(mp.h, int)