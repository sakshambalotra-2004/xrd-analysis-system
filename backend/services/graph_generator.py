"""
services/graph_generator.py
============================
Graph Visualisation Module — Stage 8 of the XRD analysis pipeline.

Produces three chart types saved as PNG files:

  1. Experimental XRD Pattern  — raw / smoothed pattern with peak markers
  2. Standard Pattern          — reference compound pattern as stem plot
  3. Overlay Chart             — experimental (blue) vs standard (red) overlay

All figures are saved to ``settings.REPORTS_GRAPHS_DIR`` and their file paths
are returned for embedding in PDF reports or serving as static assets.

Usage:
    from services.graph_generator import GraphGenerator

    gg = GraphGenerator()
    paths = gg.generate_all(
        df=smoothed_df,
        peaks_df=peaks_df,
        best_match=match_result,
        file_id="abc123",
    )
    print(paths.experimental)   # /reports/graphs/abc123_experimental.png
    print(paths.overlay)        # /reports/graphs/abc123_overlay.png
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for server-side rendering
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import settings
from services.peak_matcher import MatchResult

logger = logging.getLogger(__name__)

# Plot style constants
EXPERIMENTAL_COLOR = "#1f77b4"   # Blue
STANDARD_COLOR = "#d62728"       # Red
PEAK_MARKER_COLOR = "#2ca02c"    # Green
FIGURE_DPI = settings.REPORT_DPI
FIGURE_SIZE = (10, 4.5)          # inches


@dataclass
class GraphPaths:
    """File paths of generated graphs for one analysis run."""
    experimental: str = ""
    standard: str = ""
    overlay: str = ""


class GraphGenerator:
    """Generates and saves XRD pattern charts."""

    def __init__(self, output_dir: str | Path | None = None) -> None:
        self.out_dir = Path(output_dir or settings.REPORTS_GRAPHS_DIR)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_all(
        self,
        df: pd.DataFrame,
        peaks_df: pd.DataFrame,
        best_match: MatchResult | None,
        file_id: str,
    ) -> GraphPaths:
        """
        Generate all three chart types for one analysis run.

        Parameters
        ----------
        df : pd.DataFrame
            Smoothed XRD data.  Column names may be 'two_theta'/'intensity'
            (noise_filter output) or 'Angle'/'Intensity' (raw CSV).
        peaks_df : pd.DataFrame
            Detected peaks (two_theta, intensity).
        best_match : MatchResult | None
            Best compound match from PeakMatcher.
        file_id : str
            Unique identifier used in output filenames.

        Returns
        -------
        GraphPaths
            Absolute paths to the saved PNG files.
        """
        # FIX: resolve column names before passing to plot helpers so the
        # generator never crashes on CSVs that use 'Angle'/'Intensity' headers.
        angle_col = (
            "two_theta" if "two_theta" in df.columns
            else "Angle" if "Angle" in df.columns
            else df.columns[0]
        )
        intensity_col = (
            "intensity" if "intensity" in df.columns
            else "Intensity" if "Intensity" in df.columns
            else df.columns[1]
        )
        # Normalise to standard names for all downstream plot helpers
        df = df.rename(columns={angle_col: "two_theta", intensity_col: "intensity"})

        paths = GraphPaths()
        paths.experimental = self._plot_experimental(df, peaks_df, file_id)
        if best_match:
            paths.standard = self._plot_standard(best_match, file_id)
            paths.overlay = self._plot_overlay(df, best_match, file_id)
        return paths

    # ------------------------------------------------------------------
    # Chart generators
    # ------------------------------------------------------------------

    def _plot_experimental(
        self,
        df: pd.DataFrame,
        peaks_df: pd.DataFrame,
        file_id: str,
    ) -> str:
        """Experimental XRD pattern with detected peak markers."""
        fig, ax = plt.subplots(figsize=FIGURE_SIZE, dpi=FIGURE_DPI)
        ax.plot(df["two_theta"], df["intensity"], color=EXPERIMENTAL_COLOR, linewidth=1.2,
                label="Experimental")

        if not peaks_df.empty:
            ax.plot(
                peaks_df["two_theta"], peaks_df["intensity"],
                "^", color=PEAK_MARKER_COLOR, markersize=6, label="Detected Peaks",
            )
            for _, row in peaks_df.iterrows():
                ax.annotate(
                    f"{row['two_theta']:.2f}°",
                    xy=(row["two_theta"], row["intensity"]),
                    xytext=(0, 6), textcoords="offset points",
                    ha="center", fontsize=7, color=PEAK_MARKER_COLOR,
                )

        self._style_ax(ax, title="Experimental XRD Pattern")
        fig.tight_layout()
        out_path = str(self.out_dir / f"{file_id}_experimental.png")
        fig.savefig(out_path, bbox_inches="tight")
        plt.close(fig)
        logger.info("Saved experimental chart: %s", out_path)
        return out_path

    def _plot_standard(self, match: MatchResult, file_id: str) -> str:
        """Reference (standard) compound pattern as a stem plot."""
        std_peaks = match.matched_peaks
        if not std_peaks:
            return ""

        angles = [mp.two_theta_std for mp in std_peaks]
        intensities = [mp.intensity_std for mp in std_peaks]

        fig, ax = plt.subplots(figsize=FIGURE_SIZE, dpi=FIGURE_DPI)
        markerline, stemlines, baseline = ax.stem(
            angles, intensities, linefmt="r-",
            markerfmt="o", basefmt="k-",
        )
        # Apply exact hex colors after creation
        plt.setp(markerline, color=STANDARD_COLOR)
        plt.setp(stemlines, color=STANDARD_COLOR, linewidth=1.5)

        self._style_ax(
            ax,
            title=f"Standard Pattern — {match.compound_name} ({match.formula})",
        )
        fig.tight_layout()
        out_path = str(self.out_dir / f"{file_id}_standard.png")
        fig.savefig(out_path, bbox_inches="tight")
        plt.close(fig)
        logger.info("Saved standard chart: %s", out_path)
        return out_path
    def _plot_overlay(self, df: pd.DataFrame, match: MatchResult, file_id: str) -> str:
        """Overlay of experimental pattern vs matched standard peaks."""
        fig, ax = plt.subplots(figsize=FIGURE_SIZE, dpi=FIGURE_DPI)

        # Experimental — continuous line
        ax.plot(df["two_theta"], df["intensity"],
                color=EXPERIMENTAL_COLOR, linewidth=1.2, label="Experimental")

        # FIX: scale standard peaks against the true (raw) intensity maximum so
        # the stem heights are not under-scaled when the smoothed signal was
        # attenuated by the noise filter.
        if "raw_intensity" in df.columns:
            exp_max = df["raw_intensity"].max()
        else:
            exp_max = df["intensity"].max()

        std_peaks = match.matched_peaks
        if std_peaks:
            std_max = max(mp.intensity_std for mp in std_peaks) or 1
            scale = exp_max / std_max
            for mp in std_peaks:
                height = mp.intensity_std * scale
                ax.vlines(
                    mp.two_theta_std, 0, height,
                    colors=STANDARD_COLOR, linewidth=1.8, alpha=0.8,
                )
            ax.vlines([], [], [], colors=STANDARD_COLOR, linewidth=1.8,
                      label=f"Standard ({match.formula})")

        ax.legend(fontsize=9)
        self._style_ax(
            ax,
            title=f"Overlay Comparison — Experimental vs {match.compound_name}",
        )
        fig.tight_layout()
        out_path = str(self.out_dir / f"{file_id}_overlay.png")
        fig.savefig(out_path, bbox_inches="tight")
        plt.close(fig)
        logger.info("Saved overlay chart: %s", out_path)
        return out_path

    # ------------------------------------------------------------------
    # Shared styling
    # ------------------------------------------------------------------

    @staticmethod
    def _style_ax(ax: plt.Axes, title: str) -> None:
        ax.set_xlabel("2θ (degrees)", fontsize=11)
        ax.set_ylabel("Intensity (a.u.)", fontsize=11)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.tick_params(axis="both", labelsize=9)
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)