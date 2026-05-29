"""
tests/test_analysis.py
=======================
Unit tests for services/crystal_analyzer.py — Crystal Analysis Module.

Tests Bragg's Law, Scherrer Equation, peak shift calculation, and the full
analyze() method.
"""

import math
import pytest
import numpy as np
import pandas as pd

from services.crystal_analyzer import CrystalAnalyzer, CrystalAnalysis
from services.peak_matcher import MatchResult, MatchedPeak


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def analyzer():
    return CrystalAnalyzer(wavelength_A=1.5406, scherrer_k=0.9, bragg_n=1)


def _make_match(shifts: list[float] = None) -> MatchResult:
    """Build a mock MatchResult with controllable peak shifts."""
    base_angles = [35.60, 41.40, 60.00, 71.80]
    shifts = shifts or [0.0, 0.0, 0.0, 0.0]
    matched = [
        MatchedPeak(
            two_theta_exp=a + s,
            two_theta_std=a,
            delta_two_theta=abs(s),
            intensity_exp=80.0,
            intensity_std=100.0,
            d_spacing=1.5,
            h=1, k=0, l=1,
        )
        for a, s in zip(base_angles, shifts)
    ]
    return MatchResult(
        compound_name="Silicon Carbide",
        formula="SiC",
        crystal_system="Hexagonal",
        space_group="P63mc",
        similarity_score=100.0,
        matched_peaks=matched,
        total_standard_peaks=4,
    )


def _make_peaks_df(with_fwhm: bool = True) -> pd.DataFrame:
    data = {
        "two_theta": [35.60, 41.40, 60.00, 71.80],
        "intensity": [100.0, 60.0, 45.0, 30.0],
    }
    if with_fwhm:
        data["fwhm_deg"] = [0.30, 0.28, 0.32, 0.35]
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# Bragg's Law
# ---------------------------------------------------------------------------

class TestDSpacing:
    def test_known_value_sic_main_peak(self, analyzer):
        """SiC main peak at 35.60° → d ≈ 2.52 Å."""
        d = analyzer.d_spacing(35.60)
        assert d == pytest.approx(2.52, abs=0.02)

    def test_known_value_sio2(self, analyzer):
        """SiO2 main peak at 26.64° → d ≈ 3.34 Å."""
        d = analyzer.d_spacing(26.64)
        assert d == pytest.approx(3.34, abs=0.02)

    def test_zero_angle_returns_zero(self, analyzer):
        assert analyzer.d_spacing(0.0) == 0.0

    def test_d_decreases_with_increasing_two_theta(self, analyzer):
        angles = [20.0, 30.0, 45.0, 60.0, 80.0]
        d_vals = [analyzer.d_spacing(a) for a in angles]
        assert all(d_vals[i] > d_vals[i + 1] for i in range(len(d_vals) - 1))


# ---------------------------------------------------------------------------
# Scherrer Equation
# ---------------------------------------------------------------------------

class TestCrystalliteSize:
    def test_reasonable_size_range(self, analyzer):
        """Typical lab XRD gives 10–200 nm crystallite sizes."""
        size_A = analyzer.crystallite_size(35.60, fwhm_deg=0.3)
        size_nm = size_A / 10.0
        assert 5 < size_nm < 500

    def test_narrower_fwhm_larger_size(self, analyzer):
        """Sharper peaks → larger crystallites."""
        size_sharp = analyzer.crystallite_size(35.60, fwhm_deg=0.1)
        size_broad = analyzer.crystallite_size(35.60, fwhm_deg=0.5)
        assert size_sharp > size_broad

    def test_zero_fwhm_returns_zero(self, analyzer):
        assert analyzer.crystallite_size(35.60, fwhm_deg=0.0) == 0.0


# ---------------------------------------------------------------------------
# Peak shift & strain
# ---------------------------------------------------------------------------

class TestPeakShift:
    def test_no_shift_produces_zero_mean(self, analyzer):
        match = _make_match(shifts=[0.0, 0.0, 0.0, 0.0])
        result = analyzer.analyze(_make_peaks_df(), match)
        assert result.mean_peak_shift_deg == pytest.approx(0.0, abs=1e-6)
        assert result.strain_indicator == "None"

    def test_positive_shifts_indicate_tensile(self, analyzer):
        match = _make_match(shifts=[0.15, 0.12, 0.14, 0.13])
        result = analyzer.analyze(_make_peaks_df(), match)
        assert result.mean_peak_shift_deg > 0
        assert result.strain_indicator == "Tensile"

    def test_negative_shifts_indicate_compressive(self, analyzer):
        match = _make_match(shifts=[-0.15, -0.12, -0.14, -0.13])
        result = analyzer.analyze(_make_peaks_df(), match)
        assert result.mean_peak_shift_deg < 0
        assert result.strain_indicator == "Compressive"


# ---------------------------------------------------------------------------
# Full analyze() method
# ---------------------------------------------------------------------------

class TestAnalyzeMethod:
    def test_returns_crystal_analysis(self, analyzer):
        result = analyzer.analyze(_make_peaks_df(), _make_match())
        assert isinstance(result, CrystalAnalysis)

    def test_compound_info_populated(self, analyzer):
        result = analyzer.analyze(_make_peaks_df(), _make_match())
        assert result.primary_compound == "Silicon Carbide"
        assert result.formula == "SiC"
        assert result.crystal_system == "Hexagonal"

    def test_d_spacings_length_matches_peaks(self, analyzer):
        peaks = _make_peaks_df()
        result = analyzer.analyze(peaks, _make_match())
        assert len(result.d_spacings) == len(peaks)

    def test_crystallite_size_positive(self, analyzer):
        result = analyzer.analyze(_make_peaks_df(with_fwhm=True), _make_match())
        assert result.crystallite_size_nm > 0

    def test_empty_peaks_df_returns_defaults(self, analyzer):
        empty = pd.DataFrame(columns=["two_theta", "intensity", "fwhm_deg"])
        result = analyzer.analyze(empty, None)
        assert result.crystallite_size_nm == 0.0
        assert result.primary_compound == ""

    def test_no_match_still_computes_d_spacings(self, analyzer):
        peaks = _make_peaks_df()
        result = analyzer.analyze(peaks, best_match=None)
        assert len(result.d_spacings) == len(peaks)
        assert all(d > 0 for d in result.d_spacings)