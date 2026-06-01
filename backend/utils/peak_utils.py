"""
utils/peak_utils.py
====================
Peak utility functions shared across services.

Provides helpers for peak deduplication, merging close peaks, converting
between peak representations, and formatting peaks for API responses.
"""

import logging
from typing import Sequence

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Peak deduplication
# ---------------------------------------------------------------------------

def deduplicate_peaks(
    peaks_df: pd.DataFrame,
    tolerance_deg: float = 0.2,
) -> pd.DataFrame:
    """
    Merge peaks that are within *tolerance_deg* of each other, keeping the
    one with the highest intensity.

    Parameters
    ----------
    peaks_df : pd.DataFrame
        Must contain columns 'two_theta' and 'intensity'.
    tolerance_deg : float
        Minimum separation required between distinct peaks.

    Returns
    -------
    pd.DataFrame
        Deduplicated peaks sorted by two_theta.
    """
    if peaks_df.empty:
        return peaks_df

    df = peaks_df.sort_values("two_theta").reset_index(drop=True)
    keep_mask = np.ones(len(df), dtype=bool)

    for i in range(len(df)):
        if not keep_mask[i]:
            continue
        for j in range(i + 1, len(df)):
            if not keep_mask[j]:
                continue
            if abs(df.loc[j, "two_theta"] - df.loc[i, "two_theta"]) <= tolerance_deg:
                # Keep the stronger peak
                if df.loc[j, "intensity"] > df.loc[i, "intensity"]:
                    keep_mask[i] = False
                else:
                    keep_mask[j] = False
            else:
                break  # sorted, so no more overlaps possible

    return df[keep_mask].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Peak filtering
# ---------------------------------------------------------------------------

def filter_peaks_by_range(
    peaks_df: pd.DataFrame,
    two_theta_min: float,
    two_theta_max: float,
) -> pd.DataFrame:
    """Return only peaks within a specific 2θ range."""
    mask = peaks_df["two_theta"].between(two_theta_min, two_theta_max)
    return peaks_df[mask].reset_index(drop=True)


def filter_peaks_by_intensity(
    peaks_df: pd.DataFrame,
    min_relative_intensity: float = 5.0,
) -> pd.DataFrame:
    """
    Keep only peaks whose intensity is at least *min_relative_intensity* percent
    of the maximum peak intensity.
    """
    if peaks_df.empty:
        return peaks_df
    threshold = (min_relative_intensity / 100.0) * peaks_df["intensity"].max()
    return peaks_df[peaks_df["intensity"] >= threshold].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------

def peaks_df_to_list(peaks_df: pd.DataFrame) -> list[dict]:
    """
    Convert a peaks DataFrame to a list of dicts suitable for JSON serialisation.
    """
    cols = ["two_theta", "intensity", "fwhm_deg", "prominence", "d_spacing"]
    available = [c for c in cols if c in peaks_df.columns]
    return peaks_df[available].round(4).to_dict(orient="records")


def peaks_list_to_df(peaks: list[dict]) -> pd.DataFrame:
    """Convert a list of peak dicts back to a DataFrame."""
    return pd.DataFrame(peaks)


# ---------------------------------------------------------------------------
# Formatting for reports / API
# ---------------------------------------------------------------------------

def format_peak_table(peaks_df: pd.DataFrame, matched_peaks: list | None = None) -> list[dict]:
    """
    Produce a formatted peak table combining detected peaks with match info.

    Parameters
    ----------
    peaks_df : pd.DataFrame
        Detected experimental peaks.
    matched_peaks : list[MatchedPeak] | None
        Matched peaks from PeakMatcher.

    Returns
    -------
    list[dict]
        Each dict has keys: two_theta, d_spacing, intensity_rel, h, k, l, matched.
    """
    if peaks_df.empty:
        return []

    max_int = peaks_df["intensity"].max() or 1.0
    matched_angles = set()
    hkl_map: dict[float, tuple] = {}

    if matched_peaks:
        for mp in matched_peaks:
            matched_angles.add(round(mp.two_theta_exp, 3))
            hkl_map[round(mp.two_theta_exp, 3)] = (mp.h, mp.k, mp.l, mp.d_spacing)

    rows = []
    for _, row in peaks_df.iterrows():
        angle_key = round(float(row["two_theta"]), 3)
        is_matched = angle_key in matched_angles
        h, k, l, d = hkl_map.get(angle_key, (None, None, None, None))

        if d is None and "d_spacing" in row:
            d = round(float(row["d_spacing"]), 4)

        rows.append({
            "two_theta": round(float(row["two_theta"]), 3),
            "d_spacing": round(float(d), 4) if d else None,
            "intensity_rel": round(float(row["intensity"]) / max_int * 100, 1),
            "h": h,
            "k": k,
            "l": l,
            "matched": is_matched,
        })

    return rows


# ---------------------------------------------------------------------------
# Residual analysis
# ---------------------------------------------------------------------------

def find_unmatched_peaks(
    peaks_df: pd.DataFrame,
    matched_two_thetas: Sequence[float],
    tolerance_deg: float = 0.2,
) -> pd.DataFrame:
    """
    Return peaks from peaks_df that are NOT matched by any value in
    matched_two_thetas (used in multi-phase detection).
    """
    matched = np.array(matched_two_thetas)

    def is_unmatched(t: float) -> bool:
        if len(matched) == 0:
            return True
        return bool(np.min(np.abs(matched - t)) > tolerance_deg)

    mask = peaks_df["two_theta"].apply(is_unmatched)
    return peaks_df[mask].reset_index(drop=True)