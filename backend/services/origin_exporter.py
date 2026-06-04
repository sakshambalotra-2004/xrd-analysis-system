"""
services/origin_exporter.py
============================
High-Fidelity Open Source Plotting Engine — Drops proprietary desktop dependencies 
and builds publication-ready charts using Matplotlib and the SciencePlots engine.
"""

import logging
from pathlib import Path
import pandas as pd
import matplotlib
# Enforce headless rendering context to prevent GUI main loop threads from blocking FastAPI
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import scienceplots

from config import settings
from services.peak_matcher import MatchResult

logger = logging.getLogger(__name__)

class OriginExporter:
    """Generates high-resolution publication-quality plots using cross-platform scientific layout engines."""

    def __init__(self, output_dir: str | Path | None = None) -> None:
        self.base_dir = Path(output_dir or settings.REPORTS_BASE_DIR)
        self.project_dir = self.base_dir / "origin_files"
        self.image_dir = self.base_dir / "origin_images"
        
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.image_dir.mkdir(parents=True, exist_ok=True)

    def export_project_and_plots(
        self,
        file_id: str,
        df_smooth: pd.DataFrame,
        peaks_df: pd.DataFrame,
        best_match: MatchResult | None
    ) -> dict:
        """
        Generates an open-source publication plot and saves a structured backup data trace.

        Returns
        -------
        dict
            Paths to the data file asset and exported high-fidelity chart asset.
        """
        results = {"project_path": "", "overlay_image": ""}
        
        # Output paths matching your existing application architecture layers
        csv_backup_path = str(self.project_dir / f"xrd_data_columns_{file_id}.csv")
        image_path = str(self.image_dir / f"xrd_overlay_{file_id}.png")

        try:
            # Activate professional scientific styling mechanics (Inward ticks, high-contrast, clean lines)
            plt.style.use(['science', 'no-latex'])
            
            fig, ax = plt.subplots(figsize=(6, 4.5), dpi=300)

            # 1. Plot continuous experimental trace line
            angle_col = 'Angle' if 'Angle' in df_smooth.columns else df_smooth.columns[0]
            intensity_col = 'Intensity' if 'Intensity' in df_smooth.columns else df_smooth.columns[1]
            
            ax.plot(
                df_smooth[angle_col], 
                df_smooth[intensity_col], 
                label='Experimental Scan', 
                color='#1f77b4', 
                linewidth=1.2
            )

            # 2. Plot Standard Reference Card drops if matched candidates exist
            if best_match and best_match.matched_peaks:
                std_angles = [mp.two_theta_std for mp in best_match.matched_peaks]
                std_intensities = [mp.intensity_std for mp in best_match.matched_peaks]
                
                # Dynamic peak scaling to visually match the maximum experimental limit
                max_exp = float(df_smooth[intensity_col].max()) if not df_smooth.empty else 1.0
                max_std = max(std_intensities) if std_intensities else 1.0
                scale_factor = max_exp / max_std
                scaled_intensities = [i * scale_factor for i in std_intensities]

                # Stem creates the vertical line drop indicators characteristic of Origin crystal cards
                markerline, stemlines, baseline = ax.stem(
                    std_angles, 
                    scaled_intensities, 
                    linefmt='r--', 
                    markerfmt='ro', 
                    label=f"Standard Card: {best_match.compound_name or 'Reference'}"
                )
                plt.setp(markerline, markersize=4)
                plt.setp(stemlines, linewidth=0.8)
                plt.setp(baseline, visible=False)

            # 3. Apply strict Origin-Style Layout Formatting
            ax.set_xlabel(r'2-$\theta$ (degrees)', fontsize=10, fontweight='bold')
            ax.set_ylabel('Intensity (a.u.)', fontsize=10, fontweight='bold')
            ax.set_title(f"Phase Overlay Matrix - ID {file_id[:8]}", fontsize=11, pad=10)
            
            # Enable standard tick markers on top and right axes (Classic Origin presentation signature)
            ax.tick_params(which='both', direction='in', top=True, right=True, labelsize=9)
            
            # Format the Legend parameters cleanly
            ax.legend(loc='upper right', frameon=True, facecolor='white', edgecolor='none', fontsize=8)

            # Adjust bounding boundaries and export high-resolution asset to disk
            plt.savefig(image_path, bbox_inches='tight')
            plt.close(fig)

            # 4. Save a clean CSV tabular matrix column trace in place of the old binary .opju file
            # This allows researchers to quickly drop the raw numbers into their own software versions
            df_smooth.to_csv(csv_backup_path, index=False)

            results["project_path"] = csv_backup_path
            results["overlay_image"] = image_path
            
            logger.info("SciencePlots Vector Image rendered onto disk natively: %s", image_path)
            return results

        except Exception as exc:
            logger.error("SciencePlots Generation Framework collapsed: %s", exc, exc_info=True)
            plt.close('all')
            return results