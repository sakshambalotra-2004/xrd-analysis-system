"""
services/report_generator.py
=============================
Final Report Output Module — Stage 10 of the XRD analysis pipeline.

Generates a multi-page PDF report containing crystallographic summaries,
complete with verified compound phase and polytype notations.
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

    def _get_descriptive_phases(self, raw_phases) -> list[str]:
        """Convert plain database formula strings into clean, human-readable names with polytypes."""
        if not raw_phases:
            return []
        
        if isinstance(raw_phases, str):
            raw_phases = [p.strip() for p in raw_phases.split(",") if p.strip()]
            
        descriptive_phases = []
        for phase in raw_phases:
            base_formula = phase
            polytype_part = ""
            
            if "(" in phase and ")" in phase:
                base_formula = phase.split("(")[0].strip()
                polytype_part = phase.split("(")[1].split(")")[0].strip()
            elif "[" in phase and "]" in phase:
                base_formula = phase.split("[")[0].strip()
                polytype_part = phase.split("[")[1].split("]")[0].strip()
            
            if base_formula.lower() in ["sic", "silicon_carbide", "silicon carbide"]:
                name = "Silicon Carbide"
            elif base_formula.lower() in ["sio2", "silicon_oxide", "silicon oxide", "quartz"]:
                name = "Silicon Oxide (Quartz)"
            elif base_formula.lower() in ["nisi", "nickel_silicon", "nickel silicon"]:
                name = "Nickel Silicon"
            elif base_formula.lower() in ["nisi2"]:
                name = "Nickel Disilicide"
            elif base_formula.lower() in ["ni2si"]:
                name = "Dinickel Silicide"
            elif base_formula.lower() in ["c", "carbon", "graphite"]:
                name = "Carbon (Graphite)"
            else:
                name = base_formula
                
            if polytype_part:
                descriptive_phases.append(f"{name} ({polytype_part})")
            else:
                descriptive_phases.append(name)
                
        return descriptive_phases

    def generate(
        self,
        file_id: str,
        analysis: CrystalAnalysis,
        peaks_df: pd.DataFrame,
        graph_paths: GraphPaths,
        best_match: MatchResult | list | None,
    ) -> str:
        """Build and save the PDF report."""
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

        # 4a — ALL Raw Experimental Peaks
        if peaks_df is not None and not peaks_df.empty:
            story.extend(self._build_raw_peaks_table(peaks_df))

        # 4b — Peak Match Tables
        if best_match:
            if isinstance(best_match, list):
                for match in best_match:
                    story.extend(self._build_peak_table(match))
            else:
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
            Paragraph("XRD Compound Identification Report", self._styles["ReportTitle"]),
            Paragraph(f"File ID: {file_id}", self._styles["Subtitle"]),
            Spacer(1, 0.4 * cm),
        ]

    def _build_summary(self, a: CrystalAnalysis) -> list:
        cleaned_phases = self._get_descriptive_phases(getattr(a, "detected_phases", []))
        polytype_val = getattr(a, "polytype", "")
        compound_display = f"{a.primary_compound} ({polytype_val})" if polytype_val and a.primary_compound else (a.primary_compound or "—")

        # THE FIX: Wrap all potentially long strings in Paragraphs
        compound_para = Paragraph(compound_display, self._styles["TableCell"])
        formula_para = Paragraph(a.formula or "—", self._styles["TableCell"])
        phases_para = Paragraph(", ".join(cleaned_phases) or "—", self._styles["TableCell"])

        data = [
            ["Compound Identified", compound_para],
            ["Chemical Formula",    formula_para],
            ["Crystal System",      a.crystal_system or "—"],
            ["Space Group",         a.space_group or "—"],
            ["Confidence Score",    f"{a.confidence_score:.1f} %"],
            ["Crystallite Size",    f"{a.crystallite_size_nm:.1f} nm  ({getattr(a, 'crystallite_size_angstrom', a.crystallite_size_nm * 10):.1f} Å)"],
            ["Mean Peak Shift",     f"{a.mean_peak_shift_deg:+.4f}°"],
            ["Strain Indicator",    a.strain_indicator],
            ["Detected Phases",     phases_para],
        ]
        table = Table(data, colWidths=[6 * cm, 10 * cm], repeatRows=0)
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
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return [
            Paragraph("Analysis Summary", self._styles["SectionHead"]),
            Spacer(1, 0.2 * cm),
            table,
            Spacer(1, 0.5 * cm),
        ]

    def _build_graphs(self, paths: GraphPaths) -> list:
        story = [Paragraph("XRD Patterns", self._styles["SectionHead"]), Spacer(1, 0.2 * cm)]
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

    def _build_raw_peaks_table(self, df: pd.DataFrame) -> list:
        header = ["Peak #", "2θ (°)", "Intensity", "FWHM (°)", "Prominence"]
        rows = [header]
        
        df_reset = df.reset_index(drop=True)
        for idx, row in df_reset.iterrows():
            rows.append([
                str(idx + 1),
                f"{row.get('two_theta', 0.0):.4f}",
                f"{row.get('intensity', 0.0):.1f}",
                f"{row.get('fwhm_deg', 0.0):.4f}" if pd.notnull(row.get('fwhm_deg')) else "—",
                f"{row.get('prominence', 0.0):.1f}" if pd.notnull(row.get('prominence')) else "—",
            ])

        col_w = [2.0 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm]
        table = Table(rows, colWidths=col_w, repeatRows=1)
        style = [
            ("BACKGROUND",   (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR",    (0, 0), (-1, 0), TEXT_WHITE),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, -1), 8),
            ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
            ("BOX",          (0, 0), (-1, -1), 0.5, colors.grey),
            ("INNERGRID",    (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ]
        for i in range(1, len(rows)):
            bg = ROW_ALT if i % 2 == 0 else colors.white
            style.append(("BACKGROUND", (0, i), (-1, i), bg))
        table.setStyle(TableStyle(style))

        return [
            PageBreak(),
            Paragraph("Detected Experimental Peaks", self._styles["SectionHead"]),
            Spacer(1, 0.2 * cm),
            table,
            Spacer(1, 0.5 * cm),
        ]

    def _build_peak_table(self, match: MatchResult) -> list:
        match_polytype = getattr(match, "polytype", "")
        match_compound = getattr(match, "compound_name", "Unknown Phase")
        
        match_title = f"Reference Peak Alignments: {match_compound}"
        if match_polytype:
            match_title += f" ({match_polytype})"

        header = ["Phase/Polytype", "2θ exp (°)", "2θ std (°)", "Δ2θ (°)", "d (Å)", "I(rel.)", "h k l", "Match"]
        rows = [header]
        
        for mp in match.matched_peaks:
            raw_phase = getattr(mp, "phase_name", "") or match_compound
            cleaned_phase_list = self._get_descriptive_phases([raw_phase])
            phase_label = cleaned_phase_list[0] if cleaned_phase_list else raw_phase
            
            p_val = getattr(mp, "polytype", "") or match_polytype
            if p_val and p_val not in phase_label:
                phase_label += f" ({p_val})"
            
            # THE FIX: Wrap the phase name in a Paragraph
            phase_para = Paragraph(phase_label, self._styles["TableCellSmallLeft"])

            rows.append([
                phase_para,
                f"{mp.two_theta_exp:.3f}",
                f"{mp.two_theta_std:.3f}",
                f"{mp.delta_two_theta:+.4f}",
                f"{mp.d_spacing:.4f}",
                f"{mp.intensity_std:.0f}",
                f"({mp.h} {mp.k} {mp.l})",
                "✓",
            ])

        col_w = [3.4 * cm, 1.8 * cm, 1.8 * cm, 1.8 * cm, 1.6 * cm, 1.4 * cm, 1.8 * cm, 1.2 * cm]
        table = Table(rows, colWidths=col_w, repeatRows=1)
        style = [
            ("BACKGROUND",   (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR",    (0, 0), (-1, 0), TEXT_WHITE),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, -1), 8),
            ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
            ("ALIGN",        (0, 1), (0, -1), "LEFT"),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("BOX",          (0, 0), (-1, -1), 0.5, colors.grey),
            ("INNERGRID",    (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ]
        for i in range(1, len(rows)):
            bg = ROW_MATCH if i % 2 == 0 else colors.white
            style.append(("BACKGROUND", (0, i), (-1, i), bg))
        table.setStyle(TableStyle(style))

        return [
            Spacer(1, 0.5 * cm),
            Paragraph(match_title, self._styles["SectionHead"]),
            Spacer(1, 0.2 * cm),
            table,
            Spacer(1, 0.5 * cm),
        ]

    def _build_analysis(self, a: CrystalAnalysis) -> list:
        cleaned_phases = self._get_descriptive_phases(getattr(a, "detected_phases", []))
        
        # THE FIX: Wrap the detected phases list in a Paragraph
        phases_str = ", ".join(cleaned_phases) or "Single phase"
        phases_para = Paragraph(phases_str, self._styles["TableCell"])

        rows = [
            ["Parameter", "Value"],
            ["Crystallite Size (Scherrer)", f"{a.crystallite_size_nm:.2f} nm"],
            ["Crystallite Size (Ångströms)", f"{getattr(a, 'crystallite_size_angstrom', a.crystallite_size_nm * 10):.2f} Å"],
            ["Mean Peak Shift (Δ2θ)", f"{a.mean_peak_shift_deg:+.4f}°"],
            ["Strain Indicator", a.strain_indicator],
            ["Confidence Score", f"{a.confidence_score:.1f} %"],
            ["Detected Phases", phases_para], # Passed the Paragraph object here
        ]
        table = Table(rows, colWidths=[8 * cm, 8 * cm], repeatRows=0)
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
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return [
            PageBreak(),
            Paragraph("Analysis Results", self._styles["SectionHead"]),
            Spacer(1, 0.2 * cm),
            table,
            Spacer(1, 0.5 * cm),
        ]

    def _build_crystal_info(self, a: CrystalAnalysis) -> list:
        # THE FIX: Wrap long text fields
        compound_para = Paragraph(a.primary_compound or "—", self._styles["TableCell"])
        polytype_para = Paragraph(getattr(a, "polytype", "—") or "—", self._styles["TableCell"])
        formula_para = Paragraph(a.formula or "—", self._styles["TableCell"])

        rows = [
            ["Property", "Value"],
            ["Compound Structure", compound_para],
            ["Polytype Designation", polytype_para],
            ["Chemical Formula", formula_para],
            ["Crystal System", a.crystal_system or "—"],
            ["Space Group", a.space_group or "—"],
        ]
        table = Table(rows, colWidths=[8 * cm, 8 * cm], repeatRows=0)
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
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return [
            Paragraph("Crystal Information", self._styles["SectionHead"]),
            Spacer(1, 0.2 * cm),
            table,
        ]

    def _add_custom_styles(self) -> None:
        self._styles.add(ParagraphStyle(
            "ReportTitle", parent=self._styles["Title"], fontSize=18, textColor=HEADER_BG, spaceAfter=4,
        ))
        self._styles.add(ParagraphStyle(
            "Subtitle", parent=self._styles["Normal"], fontSize=10, textColor=colors.grey, spaceAfter=6,
        ))
        self._styles.add(ParagraphStyle(
            "SectionHead", parent=self._styles["Heading2"], fontSize=12, textColor=HEADER_BG, spaceBefore=10, spaceAfter=4,
        ))
        self._styles.add(ParagraphStyle(
            "FigCaption", parent=self._styles["Normal"], fontSize=9, textColor=colors.grey, spaceAfter=2, fontName="Helvetica-Oblique",
        ))
        
        # THE FIX: wordWrap='CJK' forces ReportLab to wrap long continuous strings properly
        self._styles.add(ParagraphStyle(
            "TableCell", parent=self._styles["Normal"], fontSize=9, leading=11, wordWrap='CJK'
        ))
        self._styles.add(ParagraphStyle(
            "TableCellSmallLeft", parent=self._styles["Normal"], fontSize=8, leading=10, alignment=0, wordWrap='CJK'
        ))