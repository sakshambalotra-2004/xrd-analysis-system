"""
tests/test_peak_detector.py
============================
Unit tests for services/peak_detector.py — Peak Detection Module.
"""

import numpy as np
import pandas as pd
import pytest

from services.peak_detector import PeakDetector, PeakDetectionConfig


@pytest.fixture
def detector():
    return PeakDetector()


def _make_df(two_theta: np.ndarray, intensity: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({"two_theta": two_theta, "intensity": intensity})


def _synthetic_pattern(n_peaks: int = 3) -> pd.DataFrame:
    """Generate a synthetic XRD pattern with known peak positions."""
    x = np.linspace(10, 80, 1000)
    y = np.zeros_like(x)
    peak_positions = [25.0, 35.6, 60.0][:n_peaks]
    for pos in peak_positions:
        y += 100 * np.exp(-((x - pos) ** 2) / (2 * 0.3 ** 2))
    y += np.random.default_rng(42).normal(0, 1, len(x)).clip(0)
    return _make_df(x, y)


class TestPeakDetectorBasic:
    def test_detects_known_peaks(self, detector):
        df = _synthetic_pattern(3)
        peaks = detector.detect(df)
        assert len(peaks) >= 3

    def test_returns_correct_columns(self, detector):
        df = _synthetic_pattern(2)
        peaks = detector.detect(df)
        for col in ("two_theta", "intensity", "fwhm_deg", "prominence"):
            assert col in peaks.columns

    def test_peaks_sorted_by_intensity_descending(self, detector):
        df = _synthetic_pattern(3)
        peaks = detector.detect(df)
        assert peaks["intensity"].is_monotonic_decreasing

    def test_peak_positions_accurate(self, detector):
        """Detected 2θ should be within ±0.5° of the true synthetic peak positions."""
        df = _synthetic_pattern(3)
        peaks = detector.detect(df)
        true_positions = {25.0, 35.6, 60.0}
        for pos in true_positions:
            close = peaks[abs(peaks["two_theta"] - pos) <= 0.5]
            assert len(close) >= 1, f"No peak found near 2θ={pos}°"

    def test_fwhm_positive(self, detector):
        df = _synthetic_pattern(3)
        peaks = detector.detect(df)
        assert (peaks["fwhm_deg"] > 0).all()


class TestEmptyAndEdgeCases:
    def test_flat_signal_returns_empty(self, detector):
        x = np.linspace(10, 80, 500)
        y = np.zeros(500)
        df = _make_df(x, y)
        peaks = detector.detect(df)
        assert peaks.empty

    def test_single_point_df(self, detector):
        df = _make_df(np.array([35.6]), np.array([100.0]))
        peaks = detector.detect(df)
        # No peaks detectable in a 1-point array — should not raise
        assert isinstance(peaks, pd.DataFrame)

    def test_noisy_low_signal(self, detector):
        """Low-amplitude noise should not produce many spurious peaks."""
        rng = np.random.default_rng(0)
        x = np.linspace(10, 80, 1000)
        y = rng.normal(0, 0.5, 1000).clip(0)
        df = _make_df(x, y)
        peaks = detector.detect(df)
        # Loose upper bound — mostly none expected
        assert len(peaks) < 10


class TestCustomConfig:
    def test_higher_threshold_fewer_peaks(self):
        df = _synthetic_pattern(3)
        default_detector = PeakDetector()
        strict_detector = PeakDetector(PeakDetectionConfig(height_fraction=0.5))
        default_peaks = default_detector.detect(df)
        strict_peaks = strict_detector.detect(df)
        assert len(strict_peaks) <= len(default_peaks)