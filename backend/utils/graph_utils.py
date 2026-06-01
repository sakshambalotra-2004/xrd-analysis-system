"""
utils/graph_utils.py
=====================
Graph utility helpers for the XRD Analysis System.

Shared functions used by graph_generator.py and any Plotly-based
interactive chart generation, covering colour palettes, axis formatting,
annotation helpers, and file-path utilities.
"""

import os
from pathlib import Path
from typing import Sequence

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np

from config import settings


# ---------------------------------------------------------------------------
# Colour palettes
# ---------------------------------------------------------------------------

PALETTE_EXPERIMENTAL = "#1f77b4"    # Matplotlib tab10 blue
PALETTE_STANDARD     = "#d62728"    # Matplotlib tab10 red
PALETTE_PEAKS        = "#2ca02c"    # Matplotlib tab10 green
PALETTE_OVERLAY_BG   = "#f8f9fa"    # Light grey background
PALETTE_GRID         = "#cccccc"

# Multi-phase palette (up to 8 distinct phases)
PHASE_COLOURS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
    "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
]


def phase_colour(index: int) -> str:
    """Return a colour from the phase palette, cycling if index > 7."""
    return PHASE_COLOURS[index % len(PHASE_COLOURS)]


# ---------------------------------------------------------------------------
# Axis / figure formatting
# ---------------------------------------------------------------------------

def style_xrd_axes(
    ax: plt.Axes,
    title: str = "",
    xlabel: str = "2θ (degrees)",
    ylabel: str = "Intensity (a.u.)",
    xlim: tuple | None = None,
    ylim: tuple | None = None,
    grid: bool = True,
) -> None:
    """
    Apply consistent XRD plot styling to a Matplotlib Axes object.

    Parameters
    ----------
    ax     : Axes to style.
    title  : Plot title.
    xlabel : X-axis label (default: "2θ (degrees)").
    ylabel : Y-axis label.
    xlim   : (min, max) x-axis limits; None → auto.
    ylim   : (min, max) y-axis limits; None → auto (always ≥ 0).
    grid   : Show grid lines.
    """
    ax.set_xlabel(xlabel, fontsize=11, labelpad=6)
    ax.set_ylabel(ylabel, fontsize=11, labelpad=6)
    if title:
        ax.set_title(title, fontsize=12, fontweight="bold", pad=8)
    ax.tick_params(axis="both", labelsize=9, direction="in")
    if grid:
        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5, color=PALETTE_GRID)
    ax.set_xlim(*xlim) if xlim else ax.set_xlim(left=0)
    ax.set_ylim(*ylim) if ylim else ax.set_ylim(bottom=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def add_peak_annotations(
    ax: plt.Axes,
    two_thetas: Sequence[float],
    intensities: Sequence[float],
    color: str = PALETTE_PEAKS,
    fontsize: int = 7,
    offset_pts: int = 5,
) -> None:
    """
    Annotate detected peaks on an Axes with their 2θ values.

    Parameters
    ----------
    two_thetas  : 2θ positions of peaks.
    intensities : Corresponding intensities (for annotation height).
    offset_pts  : Vertical offset in points above the peak.
    """
    for t, i in zip(two_thetas, intensities):
        ax.annotate(
            f"{t:.2f}°",
            xy=(t, i),
            xytext=(0, offset_pts),
            textcoords="offset points",
            ha="center",
            fontsize=fontsize,
            color=color,
            rotation=0,
        )


# ---------------------------------------------------------------------------
# File path helpers
# ---------------------------------------------------------------------------

def graph_filename(file_id: str, chart_type: str, ext: str | None = None) -> str:
    """
    Build a standardised output filename for a graph.

    Example:
        graph_filename("abc123", "overlay") → "/reports/graphs/abc123_overlay.png"
    """
    ext = ext or settings.REPORT_GRAPH_FORMAT
    filename = f"{file_id}_{chart_type}.{ext}"
    return str(Path(settings.REPORTS_GRAPHS_DIR) / filename)


def ensure_output_dirs() -> None:
    """Create all report output directories if they do not exist."""
    for path in [
        settings.REPORTS_BASE_DIR,
        settings.REPORTS_GRAPHS_DIR,
        settings.REPORTS_PDF_DIR,
        settings.REPORTS_OVERLAY_DIR,
    ]:
        Path(path).mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Legend helpers
# ---------------------------------------------------------------------------

def build_compound_legend_label(compound: str, formula: str, score: float) -> str:
    """
    Format a legend label for a matched compound.

    Example: "Silicon Carbide (SiC) — 94.0%"
    """
    return f"{compound} ({formula}) — {score:.1f}%"


# ---------------------------------------------------------------------------
# Intensity normalisation for display
# ---------------------------------------------------------------------------

def normalise_for_display(intensity: np.ndarray, target_max: float = 100.0) -> np.ndarray:
    """Scale intensity array so the maximum equals *target_max*."""
    max_val = intensity.max()
    if max_val == 0:
        return intensity.copy()
    return intensity / max_val * target_max