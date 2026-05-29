"""
services/report_generator.py
=============================
Final Report Output Module — Stage 10 of the XRD analysis pipeline.

Generates a multi-page PDF report containing:
  - Summary header   : compound name, formula, crystal system, confidence
  - Graph page       : experimental pattern, standard pattern, overlay chart
  - Peak match table : 2θ, d(Å), I(rel.), h, k, l, match status
  - Analysis results : crystallite size, peak shift, detected phases
  - Crystal info     : space group, lattice system, peak indexing

Uses ReportLab for PDF generation.

Usage:
    from services.report_generator import ReportGenerator

    gen = ReportGenerator()
    pdf_path = gen.generate(
        file_id="abc123",
        analysis=crystal_analysis,
        peaks_df=peaks_df,
        graph_paths=graph_paths,
        best_match=match_result,
    )
    print(pdf_path)   # /reports/pdf_reports/abc123_report.pdf
"""

import logging
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config import settings
from services.crystal_analyzer import CrystalAnalysis
from services.graph_generator import GraphPaths
from services.peak_matcher import MatchResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
HEADER_BG   = colors.HexColor("#1B3A6B")
SUBHEAD_BG  = colors.HexColor("#2E6DB4")
ROW_ALT     = colors.HexColor("#EBF3FA")
ROW_MATCH   = colors.HexColor("#D4EDDA")
ROW_MISS    = colors.HexColor("#FDE8E8")
TEXT_WHITE  = colors.white
TEXT_DARK   = colors.HexColor("#1A1A2E")

PAGE_W, PAGE_H = A4
MARGIN = 2.0 * cm


class ReportGenerator:
    """Builds a PDF analysis report for one XRD sample."""

    def __init__(self, output_dir: str | Path | None = None) -> None:
        self.out_dir = Path(output_dir or settings.REPORTS_PDF_DIR)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self._styles = getSampleStyleSheet()
        self._add_custom_styles()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        file_id: str,
        analysis: CrystalAnalysis,
        peaks_df: pd.DataFrame,
        graph_paths: GraphPaths,
        best_match: MatchResult | None,
    ) -> str:
        """
        Build and save the PDF report.

        Returns
        -------
        str
            Absolute path of the saved PDF file.
        """
        out_path = str(self.out_dir / f"{file_id}_report.pdf")
        doc = SimpleDocTemplate(
            out_path,
            pagesize=A4,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            topMargin=MARGIN,
            bottomMargin=MARGIN,
        )

        story = []

        # 1 — Title
        story.extend(self._build_title(file_id))

        # 2 — Summary card
        story.extend(self._build_summary(analysis))

        # 3 — Graphs
        story.extend(self._build_graphs(graph_paths))

        # 4 — Peak match table
        if best_match:
            story.extend(self._build_peak_table(best_match))

        # 5 — Analysis results
        story.extend(self._build_analysis(analysis))

        # 6 — Crystal info
        story.extend(self._build_crystal_info(analysis))

        doc.build(story)
        logger.info("PDF report saved: %s", out_path)
        return out_path

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _build_title(self, file_id: str) -> list:
        return [
            Paragraph("XRD Compound Identification Report",
                      self._styles["ReportTitle"]),
            Paragraph(f"File ID: {file_id}", self._styles["Subtitle"]),
            Spacer(1, 0.4 * cm),
        ]

    def _build_summary(self, a: CrystalAnalysis) -> list:
        data = [
            ["Compound Identified", a.primary_compound or "—"],
            ["Chemical Formula",    a.formula or "—"],
            ["Crystal System",      a.crystal_system or "—"],
            ["Space Group",         a.space_group or "—"],
            ["Confidence Score",    f"{a.confidence_score:.1f} %"],
            ["Crystallite Size",    f"{a.crystallite_size_nm:.1f} nm  ({a.crystallite_size_angstrom:.1f} Å)"],
            ["Mean Peak Shift",     f"{a.mean_peak_shift_deg:+.4f}°"],
            ["Strain Indicator",    a.strain_indicator],
            ["Detected Phases",     ", ".join(a.detected_phases) or "—"],
        ]
        table = Table(data, colWidths=[6 * cm, 10 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (0, -1), SUBHEAD_BG),
            ("TEXTCOLOR",   (0, 0), (0, -1), TEXT_WHITE),
            ("FONTNAME",    (0, 0), (-1, -1), "Helvetica"),
            ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (1, 0), (1, -1), [colors.white, ROW_ALT]),
            ("BOX",         (0, 0), (-1, -1), 0.5, colors.grey),
            ("INNERGRID",   (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ]))
        return [
            Paragraph("Analysis Summary", self._styles["SectionHead"]),
            Spacer(1, 0.2 * cm),
            table,
            Spacer(1, 0.5 * cm),
        ]

    def _build_graphs(self, paths: GraphPaths) -> list:
        story = [Paragraph("XRD Patterns", self._styles["SectionHead"]),
                 Spacer(1, 0.2 * cm)]
        img_w = PAGE_W - 2 * MARGIN
        for label, fpath in [
            ("Experimental XRD Pattern", paths.experimental),
            ("Standard Reference Pattern", paths.standard),
            ("Overlay Comparison", paths.overlay),
        ]:
            if fpath and Path(fpath).exists():
                story.append(Paragraph(label, self._styles["FigCaption"]))
                story.append(Image(fpath, width=img_w, height=img_w * 0.45))
                story.append(Spacer(1, 0.3 * cm))
        return story

    def _build_peak_table(self, match: MatchResult) -> list:
        header = ["2θ exp (°)", "2θ std (°)", "Δ2θ (°)", "d (Å)", "I(rel.)", "h", "k", "l", "Match"]
        rows = [header]
        for mp in match.matched_peaks:
            rows.append([
                f"{mp.two_theta_exp:.3f}",
                f"{mp.two_theta_std:.3f}",
                f"{mp.delta_two_theta:+.4f}",
                f"{mp.d_spacing:.4f}",
                f"{mp.intensity_std:.0f}",
                str(mp.h), str(mp.k), str(mp.l),
                "✓",
            ])

        col_w = [(PAGE_W - 2 * MARGIN) / len(header)] * len(header)
        table = Table(rows, colWidths=col_w)
        style = [
            ("BACKGROUND",   (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR",    (0, 0), (-1, 0), TEXT_WHITE),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, -1), 8),
            ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
            ("BOX",          (0, 0), (-1, -1), 0.5, colors.grey),
            ("INNERGRID",    (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ("TOPPADDING",   (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ]
        for i in range(1, len(rows)):
            bg = ROW_MATCH if i % 2 == 0 else colors.white
            style.append(("BACKGROUND", (0, i), (-1, i), bg))
        table.setStyle(TableStyle(style))

        return [
            PageBreak(),
            Paragraph("Peak Match Table", self._styles["SectionHead"]),
            Spacer(1, 0.2 * cm),
            table,
            Spacer(1, 0.5 * cm),
        ]

    def _build_analysis(self, a: CrystalAnalysis) -> list:
        rows = [
            ["Parameter", "Value"],
            ["Crystallite Size (Scherrer)", f"{a.crystallite_size_nm:.2f} nm"],
            ["Crystallite Size (Ångströms)", f"{a.crystallite_size_angstrom:.2f} Å"],
            ["Mean Peak Shift (Δ2θ)", f"{a.mean_peak_shift_deg:+.4f}°"],
            ["Strain Indicator", a.strain_indicator],
            ["Confidence Score", f"{a.confidence_score:.1f} %"],
            ["Detected Phases", ", ".join(a.detected_phases) or "Single phase"],
        ]
        table = Table(rows, colWidths=[8 * cm, 8 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0), SUBHEAD_BG),
            ("TEXTCOLOR",   (0, 0), (-1, 0), TEXT_WHITE),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
            ("BOX",         (0, 0), (-1, -1), 0.5, colors.grey),
            ("INNERGRID",   (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING",  (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0,0), (-1, -1), 4),
        ]))
        return [
            Paragraph("Analysis Results", self._styles["SectionHead"]),
            Spacer(1, 0.2 * cm),
            table,
            Spacer(1, 0.5 * cm),
        ]

    def _build_crystal_info(self, a: CrystalAnalysis) -> list:
        rows = [
            ["Property", "Value"],
            ["Compound", a.primary_compound or "—"],
            ["Formula", a.formula or "—"],
            ["Crystal System", a.crystal_system or "—"],
            ["Space Group", a.space_group or "—"],
        ]
        table = Table(rows, colWidths=[8 * cm, 8 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0), SUBHEAD_BG),
            ("TEXTCOLOR",   (0, 0), (-1, 0), TEXT_WHITE),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
            ("BOX",         (0, 0), (-1, -1), 0.5, colors.grey),
            ("INNERGRID",   (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING",  (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0,0), (-1, -1), 4),
        ]))
        return [
            Paragraph("Crystal Information", self._styles["SectionHead"]),
            Spacer(1, 0.2 * cm),
            table,
        ]

    # ------------------------------------------------------------------
    # Custom paragraph styles
    # ------------------------------------------------------------------

    def _add_custom_styles(self) -> None:
        self._styles.add(ParagraphStyle(
            "ReportTitle",
            parent=self._styles["Title"],
            fontSize=18, textColor=HEADER_BG, spaceAfter=4,
        ))
        self._styles.add(ParagraphStyle(
            "Subtitle",
            parent=self._styles["Normal"],
            fontSize=10, textColor=colors.grey, spaceAfter=6,
        ))
        self._styles.add(ParagraphStyle(
            "SectionHead",
            parent=self._styles["Heading2"],
            fontSize=12, textColor=HEADER_BG, spaceBefore=10, spaceAfter=4,
        ))
        self._styles.add(ParagraphStyle(
            "FigCaption",
            parent=self._styles["Normal"],
            fontSize=9, textColor=colors.grey, spaceAfter=2, fontName="Helvetica-Oblique",
        ))