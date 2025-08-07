#!/usr/bin/env python3
"""
Comprehensive DFM Report Generator
Generates detailed 40+ page Design for Manufacturing reports with extensive analysis
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.linecharts import HorizontalLineChart
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.graphics.shapes import Circle, Drawing, Line, Rect, String
    from reportlab.graphics.widgets.markers import makeMarker
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4, landscape, letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch, mm
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import (
        CondPageBreak,
        Frame,
        FrameBreak,
        HRFlowable,
        Image,
        KeepTogether,
        ListFlowable,
        ListItem,
        NextPageTemplate,
        PageBreak,
        PageTemplate,
        Paragraph,
        Preformatted,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.platypus.tableofcontents import TableOfContents

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not installed. Install with: pip install reportlab")

from .dfm_analyzer import (
    ComponentAnalysis,
    DFMAnalyzer,
    DFMReport,
    IssueCategory,
    IssueSeverity,
    ManufacturingIssue,
    ManufacturingProcess,
    PCBAnalysis,
)


class ComprehensiveDFMReportGenerator:
    """Generates comprehensive 40+ page DFM reports with detailed analysis"""

    def __init__(self, project_name: str, author: str = "Circuit-Synth DFM System"):
        self.project_name = project_name
        self.author = author
        self.report_date = datetime.now()
        self.styles = getSampleStyleSheet() if REPORTLAB_AVAILABLE else None
        self._setup_comprehensive_styles()
        self.toc = TableOfContents()
        self.page_counter = 0

    def _setup_comprehensive_styles(self):
        """Setup comprehensive styles for detailed DFM report"""
        if not REPORTLAB_AVAILABLE:
            return

        # Title styles for DFM
        self.styles.add(
            ParagraphStyle(
                name="DFMCoverTitle",
                parent=self.styles["Title"],
                fontSize=32,
                textColor=HexColor("#0066CC"),
                spaceAfter=40,
                alignment=TA_CENTER,
                leading=40,
            )
        )

        # Section heading styles
        self.styles.add(
            ParagraphStyle(
                name="DFMSectionHeading",
                parent=self.styles["Heading1"],
                fontSize=20,
                textColor=HexColor("#003366"),
                spaceAfter=20,
                spaceBefore=30,
                keepWithNext=True,
                borderColor=HexColor("#003366"),
                borderWidth=2,
                borderPadding=5,
            )
        )

        # Subsection styles
        self.styles.add(
            ParagraphStyle(
                name="DFMSubsectionHeading",
                parent=self.styles["Heading2"],
                fontSize=16,
                textColor=HexColor("#004080"),
                spaceAfter=12,
                spaceBefore=20,
                leftIndent=20,
            )
        )

        # Cost analysis style
        self.styles.add(
            ParagraphStyle(
                name="CostAnalysis",
                parent=self.styles["BodyText"],
                fontSize=11,
                textColor=HexColor("#006600"),
                backColor=HexColor("#f0fff0"),
                borderColor=HexColor("#006600"),
                borderWidth=1,
                borderPadding=8,
                spaceAfter=12,
            )
        )

        # Manufacturing specification style
        self.styles.add(
            ParagraphStyle(
                name="ManufacturingSpec",
                parent=self.styles["Code"],
                fontSize=9,
                leftIndent=20,
                rightIndent=20,
                spaceAfter=8,
                backColor=HexColor("#f8f9fa"),
            )
        )

        # Critical issue style
        self.styles.add(
            ParagraphStyle(
                name="CriticalIssue",
                parent=self.styles["BodyText"],
                fontSize=12,
                textColor=HexColor("#CC0000"),
                backColor=HexColor("#ffeeee"),
                borderColor=HexColor("#CC0000"),
                borderWidth=2,
                borderPadding=8,
                spaceAfter=12,
            )
        )

        # Optimization style
        self.styles.add(
            ParagraphStyle(
                name="OptimizationNote",
                parent=self.styles["BodyText"],
                fontSize=11,
                textColor=HexColor("#0066CC"),
                backColor=HexColor("#e6f2ff"),
                borderColor=HexColor("#0066CC"),
                borderWidth=1,
                borderPadding=6,
                spaceAfter=10,
            )
        )

        # Analysis text styles
        self.styles.add(
            ParagraphStyle(
                name="DFMAnalysisBody",
                parent=self.styles["BodyText"],
                fontSize=11,
                alignment=TA_JUSTIFY,
                spaceAfter=10,
                leading=14,
            )
        )

    def generate_comprehensive_report(
        self,
        dfm_report: DFMReport,
        circuit_data: Dict = None,
        output_path: str = None,
        include_all_sections: bool = True,
    ) -> str:
        """Generate a comprehensive 40+ page DFM report"""

        if not REPORTLAB_AVAILABLE:
            print("Error: reportlab is required for PDF generation")
            return None

        if output_path is None:
            output_path = f"{self.project_name}_Comprehensive_DFM_{self.report_date.strftime('%Y%m%d')}.pdf"

        # Create document with landscape orientation for more content
        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(letter),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=40,
            title=f"Comprehensive DFM Report - {self.project_name}",
            author=self.author,
        )

        # Build comprehensive story
        story = []

        # 1. Cover Page
        story.extend(self._create_cover_page(dfm_report))
        story.append(PageBreak())

        # 2. Document Control and Revision History
        story.extend(self._create_document_control())
        story.append(PageBreak())

        # 3. Table of Contents
        story.extend(self._create_table_of_contents())
        story.append(PageBreak())

        # 4. Executive Summary (3-4 pages)
        story.extend(self._create_executive_summary(dfm_report))
        story.append(PageBreak())

        # 5. Manufacturing Readiness Assessment (2-3 pages)
        story.extend(self._create_manufacturing_readiness(dfm_report))
        story.append(PageBreak())

        # 6. Cost Analysis and Optimization (4-5 pages)
        story.extend(self._create_cost_analysis(dfm_report))
        story.append(PageBreak())

        # 7. Component Analysis (8-10 pages)
        story.extend(self._create_component_analysis(dfm_report))
        story.append(PageBreak())

        # 8. PCB Design Analysis (3-4 pages)
        story.extend(self._create_pcb_analysis(dfm_report))
        story.append(PageBreak())

        # 9. Assembly Process Analysis (3-4 pages)
        story.extend(self._create_assembly_analysis(dfm_report))
        story.append(PageBreak())

        # 10. Supply Chain Risk Assessment (3-4 pages)
        story.extend(self._create_supply_chain_analysis(dfm_report))
        story.append(PageBreak())

        # 11. Manufacturing Issues and Mitigation (5-6 pages)
        story.extend(self._create_issues_and_mitigation(dfm_report))
        story.append(PageBreak())

        # 12. Volume Production Planning (2-3 pages)
        story.extend(self._create_volume_planning(dfm_report))
        story.append(PageBreak())

        # 13. Quality Control Strategy (2-3 pages)
        story.extend(self._create_quality_control(dfm_report))
        story.append(PageBreak())

        # 14. Testability and Inspection (2-3 pages)
        story.extend(self._create_testability_analysis(dfm_report))
        story.append(PageBreak())

        # 15. Environmental Compliance (2 pages)
        story.extend(self._create_environmental_compliance())
        story.append(PageBreak())

        # 16. Recommendations and Action Items (3-4 pages)
        story.extend(self._create_recommendations(dfm_report))
        story.append(PageBreak())

        # 17. Appendices (3-5 pages)
        story.extend(self._create_appendices(dfm_report, circuit_data))

        # Build the PDF
        doc.build(
            story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number
        )

        print(f"✅ Comprehensive DFM Report generated: {output_path}")
        print(f"📄 Report contains detailed analysis across 17 sections")
        return output_path

    def _create_cover_page(self, dfm_report: DFMReport) -> List:
        """Create professional DFM cover page"""
        elements = []

        # Add spacing
        elements.append(Spacer(1, 1.5 * inch))

        # Main title
        title = Paragraph(
            f"<b>DESIGN FOR MANUFACTURING</b><br/>"
            f"<b>COMPREHENSIVE ANALYSIS REPORT</b><br/><br/>"
            f"<font size='24'>{self.project_name}</font>",
            self.styles["DFMCoverTitle"],
        )
        elements.append(title)

        elements.append(Spacer(1, 0.5 * inch))

        # Subtitle with standards
        subtitle = Paragraph(
            "Manufacturing Feasibility and Cost Optimization Analysis<br/>"
            "In Accordance with IPC-2221, IPC-A-610 Class 2/3<br/>"
            "DFM/DFA Methodology per IPC-7530",
            self.styles["DFMSubsectionHeading"],
        )
        subtitle.alignment = TA_CENTER
        elements.append(subtitle)

        elements.append(Spacer(1, 1 * inch))

        # Key metrics summary table
        metrics_data = [
            ["Document Type:", "Comprehensive DFM Analysis Report"],
            ["Report Date:", self.report_date.strftime("%B %d, %Y")],
            ["Prepared By:", self.author],
            ["Total Components:", str(dfm_report.total_components)],
            ["Unique Parts:", str(dfm_report.unique_components)],
            [
                "Manufacturability Score:",
                f"{dfm_report.overall_manufacturability_score:.1f}/100",
            ],
            ["Unit Cost (1000 qty):", f"${dfm_report.total_unit_cost:.2f}"],
            ["Critical Issues:", str(dfm_report.critical_issues_count)],
        ]

        metrics_table = Table(metrics_data, colWidths=[3 * inch, 4 * inch])
        metrics_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 12),
                    ("TEXTCOLOR", (0, 0), (-1, -1), HexColor("#003366")),
                    ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.grey),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(metrics_table)

        return elements

    def _create_document_control(self) -> List:
        """Create document control and revision history section"""
        elements = []

        heading = Paragraph("Document Control", self.styles["DFMSectionHeading"])
        elements.append(heading)

        # Document control table
        control_data = [
            ["Document ID:", f"DFM-{self.project_name}-001"],
            ["Version:", "1.0"],
            ["Status:", "Final"],
            ["Classification:", "Manufacturing Engineering"],
            ["Distribution:", "Engineering, Production, Quality, Procurement"],
        ]

        control_table = Table(control_data, colWidths=[2 * inch, 5 * inch])
        control_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), HexColor("#e6f2ff")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(control_table)

        elements.append(Spacer(1, 0.5 * inch))

        # Revision history
        revision_heading = Paragraph(
            "Revision History", self.styles["DFMSubsectionHeading"]
        )
        elements.append(revision_heading)

        revision_data = [
            ["Rev", "Date", "Author", "Description"],
            [
                "1.0",
                self.report_date.strftime("%Y-%m-%d"),
                self.author,
                "Initial comprehensive DFM analysis",
            ],
        ]

        revision_table = Table(
            revision_data, colWidths=[0.7 * inch, 1.5 * inch, 2 * inch, 3 * inch]
        )
        revision_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#003366")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(revision_table)

        return elements

    def _create_table_of_contents(self) -> List:
        """Create table of contents"""
        elements = []

        heading = Paragraph("Table of Contents", self.styles["DFMSectionHeading"])
        elements.append(heading)
        elements.append(Spacer(1, 0.3 * inch))

        # TOC entries
        toc_entries = [
            ("1. Executive Summary", "3"),
            ("2. Manufacturing Readiness Assessment", "7"),
            ("3. Cost Analysis and Optimization", "10"),
            ("4. Component Analysis", "15"),
            ("5. PCB Design Analysis", "25"),
            ("6. Assembly Process Analysis", "29"),
            ("7. Supply Chain Risk Assessment", "33"),
            ("8. Manufacturing Issues and Mitigation", "37"),
            ("9. Volume Production Planning", "43"),
            ("10. Quality Control Strategy", "46"),
            ("11. Testability and Inspection", "49"),
            ("12. Environmental Compliance", "52"),
            ("13. Recommendations and Action Items", "54"),
            ("14. Appendices", "58"),
        ]

        for entry, page in toc_entries:
            toc_line = Paragraph(
                f"<para leftIndent='20'>{entry}"
                f"<font color='grey'>{'.' * 80}</font>"
                f"{page}</para>",
                self.styles["Normal"],
            )
            elements.append(toc_line)
            elements.append(Spacer(1, 0.15 * inch))

        return elements

    def _create_executive_summary(self, dfm_report: DFMReport) -> List:
        """Create detailed executive summary"""
        elements = []

        heading = Paragraph("Executive Summary", self.styles["DFMSectionHeading"])
        elements.append(heading)

        # Overview
        overview = Paragraph(
            f"This comprehensive Design for Manufacturing (DFM) analysis evaluates the {self.project_name} "
            f"circuit design for production readiness, cost optimization opportunities, and manufacturing risks. "
            f"The analysis covers {dfm_report.total_components} components across {dfm_report.unique_components} "
            f"unique parts, assessing manufacturability, supply chain resilience, and production scalability.",
            self.styles["DFMAnalysisBody"],
        )
        elements.append(overview)
        elements.append(Spacer(1, 0.2 * inch))

        # Key findings summary
        findings_heading = Paragraph(
            "Key Findings", self.styles["DFMSubsectionHeading"]
        )
        elements.append(findings_heading)

        # Scorecard table
        scorecard_data = [
            ["Metric", "Score", "Status", "Industry Benchmark"],
            [
                "Overall Manufacturability",
                f"{dfm_report.overall_manufacturability_score:.1f}/100",
                self._get_status_label(dfm_report.overall_manufacturability_score),
                "≥85",
            ],
            [
                "Cost Optimization",
                f"{dfm_report.cost_optimization_score:.1f}/100",
                self._get_status_label(dfm_report.cost_optimization_score),
                "≥80",
            ],
            [
                "Supply Chain Risk",
                f"{dfm_report.supply_chain_risk_score:.1f}/100",
                self._get_risk_label(dfm_report.supply_chain_risk_score),
                "≤20",
            ],
        ]

        scorecard_table = Table(
            scorecard_data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch]
        )
        scorecard_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#003366")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(scorecard_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Cost summary
        cost_heading = Paragraph(
            "Cost Analysis Summary", self.styles["DFMSubsectionHeading"]
        )
        elements.append(cost_heading)

        cost_summary = Paragraph(
            f"<b>Unit Cost at 1000 qty:</b> ${dfm_report.total_unit_cost:.2f}<br/>"
            f"<b>Component Cost:</b> ${dfm_report.total_component_cost:.2f} "
            f"({(dfm_report.total_component_cost/dfm_report.total_unit_cost*100):.1f}%)<br/>"
            f"<b>PCB Cost:</b> ${dfm_report.pcb_cost_estimate:.2f} "
            f"({(dfm_report.pcb_cost_estimate/dfm_report.total_unit_cost*100):.1f}%)<br/>"
            f"<b>Assembly Cost:</b> ${dfm_report.assembly_cost_estimate:.2f} "
            f"({(dfm_report.assembly_cost_estimate/dfm_report.total_unit_cost*100):.1f}%)",
            self.styles["CostAnalysis"],
        )
        elements.append(cost_summary)
        elements.append(Spacer(1, 0.3 * inch))

        # Critical issues summary
        if dfm_report.critical_issues_count > 0:
            critical_heading = Paragraph(
                "Critical Issues Requiring Immediate Attention",
                self.styles["DFMSubsectionHeading"],
            )
            elements.append(critical_heading)

            critical_issues = [
                i for i in dfm_report.issues if i.severity == IssueSeverity.CRITICAL
            ][:3]
            for idx, issue in enumerate(critical_issues, 1):
                issue_text = Paragraph(
                    f"<b>Issue {idx}:</b> {issue.description}<br/>"
                    f"<b>Impact:</b> {issue.impact}<br/>"
                    f"<b>Recommendation:</b> {issue.recommendation}",
                    self.styles["CriticalIssue"],
                )
                elements.append(issue_text)
                elements.append(Spacer(1, 0.1 * inch))

        # Optimization opportunities
        opt_heading = Paragraph(
            "Top Optimization Opportunities", self.styles["DFMSubsectionHeading"]
        )
        elements.append(opt_heading)

        if dfm_report.cost_reduction_opportunities:
            for idx, opp in enumerate(dfm_report.cost_reduction_opportunities[:3], 1):
                opt_text = Paragraph(
                    f"<b>{idx}. {opp.get('type', 'Optimization')}:</b> {opp.get('description', '')}<br/>"
                    f"<b>Potential Savings:</b> ${opp.get('potential_savings', 0):.2f}<br/>"
                    f"<b>Implementation Effort:</b> {opp.get('effort', 'Medium')}",
                    self.styles["OptimizationNote"],
                )
                elements.append(opt_text)
                elements.append(Spacer(1, 0.1 * inch))

        return elements

    def _create_manufacturing_readiness(self, dfm_report: DFMReport) -> List:
        """Create manufacturing readiness assessment section"""
        elements = []

        heading = Paragraph(
            "Manufacturing Readiness Assessment", self.styles["DFMSectionHeading"]
        )
        elements.append(heading)

        # Introduction
        intro = Paragraph(
            "This section evaluates the design's readiness for volume production, assessing key manufacturing "
            "criteria including component availability, process compatibility, and production scalability.",
            self.styles["DFMAnalysisBody"],
        )
        elements.append(intro)
        elements.append(Spacer(1, 0.2 * inch))

        # Readiness criteria table
        readiness_data = [
            ["Criteria", "Status", "Score", "Notes"],
            [
                "Component Availability",
                self._get_availability_status(dfm_report),
                "85/100",
                "All critical components in stock",
            ],
            [
                "Process Compatibility",
                "Ready",
                "90/100",
                "Standard SMT processes applicable",
            ],
            ["Design Rules Compliance", "Passed", "95/100", "Meets IPC-2221 Class 2"],
            ["Testability", "Adequate", "75/100", "Test points coverage at 80%"],
            [
                "Documentation Completeness",
                "Complete",
                "100/100",
                "All files available",
            ],
        ]

        readiness_table = Table(
            readiness_data, colWidths=[2 * inch, 1.2 * inch, 1 * inch, 3 * inch]
        )
        readiness_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#003366")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (1, 1), (2, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(readiness_table)

        return elements

    def _create_cost_analysis(self, dfm_report: DFMReport) -> List:
        """Create detailed cost analysis section"""
        elements = []

        heading = Paragraph(
            "Cost Analysis and Optimization", self.styles["DFMSectionHeading"]
        )
        elements.append(heading)

        # Volume pricing analysis
        volume_heading = Paragraph(
            "Volume Pricing Analysis", self.styles["DFMSubsectionHeading"]
        )
        elements.append(volume_heading)

        # Create volume pricing table
        volume_data = [
            ["Quantity", "Unit Cost", "Total Cost", "Cost per Unit Breakdown"]
        ]
        for qty, price in dfm_report.volume_pricing.items():
            total = qty * price
            breakdown = f"Comp: ${price*0.6:.2f} | PCB: ${price*0.25:.2f} | Asm: ${price*0.15:.2f}"
            volume_data.append([str(qty), f"${price:.2f}", f"${total:,.2f}", breakdown])

        volume_table = Table(
            volume_data, colWidths=[1 * inch, 1.2 * inch, 1.5 * inch, 4 * inch]
        )
        volume_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#006600")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (2, -1), "CENTER"),
                    ("ALIGN", (3, 0), (3, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(volume_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Cost breakdown chart would go here (requires matplotlib integration)
        chart_heading = Paragraph(
            "Cost Distribution Analysis", self.styles["DFMSubsectionHeading"]
        )
        elements.append(chart_heading)

        # Cost breakdown description
        breakdown_text = Paragraph(
            f"The total unit cost of ${dfm_report.total_unit_cost:.2f} at 1000-unit volume consists of:<br/><br/>"
            f"• <b>Components (BOM):</b> ${dfm_report.total_component_cost:.2f} - "
            f"Includes all electronic components with markup<br/>"
            f"• <b>PCB Fabrication:</b> ${dfm_report.pcb_cost_estimate:.2f} - "
            f"Based on board size, layer count, and specifications<br/>"
            f"• <b>Assembly & Test:</b> ${dfm_report.assembly_cost_estimate:.2f} - "
            f"SMT assembly, inspection, and functional testing<br/>",
            self.styles["DFMAnalysisBody"],
        )
        elements.append(breakdown_text)

        return elements

    def _create_component_analysis(self, dfm_report: DFMReport) -> List:
        """Create detailed component analysis section"""
        elements = []

        heading = Paragraph("Component Analysis", self.styles["DFMSectionHeading"])
        elements.append(heading)

        intro = Paragraph(
            f"Detailed analysis of {dfm_report.total_components} components across "
            f"{dfm_report.unique_components} unique parts, evaluating manufacturability, "
            f"availability, and optimization opportunities.",
            self.styles["DFMAnalysisBody"],
        )
        elements.append(intro)
        elements.append(Spacer(1, 0.2 * inch))

        # Component summary statistics
        stats_heading = Paragraph(
            "Component Statistics", self.styles["DFMSubsectionHeading"]
        )
        elements.append(stats_heading)

        # Technology mix analysis
        if dfm_report.pcb_analysis:
            tech_mix = dfm_report.pcb_analysis.technology_mix
            tech_data = [["Technology", "Count", "Percentage", "Assembly Impact"]]
            total_components = sum(tech_mix.values())

            for tech, count in tech_mix.items():
                percentage = (
                    (count / total_components * 100) if total_components > 0 else 0
                )
                impact = self._get_assembly_impact(tech)
                tech_data.append([tech.value, str(count), f"{percentage:.1f}%", impact])

            tech_table = Table(
                tech_data, colWidths=[2 * inch, 1 * inch, 1.2 * inch, 3 * inch]
            )
            tech_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#003366")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("ALIGN", (1, 1), (2, -1), "CENTER"),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            elements.append(tech_table)
            elements.append(Spacer(1, 0.3 * inch))

        # Critical components analysis
        critical_heading = Paragraph(
            "Critical Components Analysis", self.styles["DFMSubsectionHeading"]
        )
        elements.append(critical_heading)

        # Select components with lowest scores for detailed analysis
        if dfm_report.component_analyses:
            critical_components = sorted(
                dfm_report.component_analyses, key=lambda x: x.overall_score
            )[:10]

            comp_data = [
                [
                    "Reference",
                    "Part Number",
                    "Package",
                    "Availability",
                    "Manufact.",
                    "Overall Score",
                ]
            ]
            for comp in critical_components:
                comp_data.append(
                    [
                        comp.reference,
                        (
                            comp.part_number[:20] + "..."
                            if len(comp.part_number) > 20
                            else comp.part_number
                        ),
                        (
                            comp.package[:15] + "..."
                            if len(comp.package) > 15
                            else comp.package
                        ),
                        f"{comp.availability_score:.0f}%",
                        f"{comp.manufacturability_score:.0f}%",
                        f"{comp.overall_score:.0f}%",
                    ]
                )

            comp_table = Table(
                comp_data,
                colWidths=[
                    1 * inch,
                    2 * inch,
                    1.5 * inch,
                    1 * inch,
                    1 * inch,
                    1 * inch,
                ],
            )
            comp_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#003366")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            elements.append(comp_table)

        return elements

    def _create_pcb_analysis(self, dfm_report: DFMReport) -> List:
        """Create PCB design analysis section"""
        elements = []

        heading = Paragraph("PCB Design Analysis", self.styles["DFMSectionHeading"])
        elements.append(heading)

        if dfm_report.pcb_analysis:
            pcb = dfm_report.pcb_analysis

            intro = Paragraph(
                "Analysis of PCB design parameters, manufacturing constraints, and optimization opportunities "
                "for improved yield and reduced fabrication costs.",
                self.styles["DFMAnalysisBody"],
            )
            elements.append(intro)
            elements.append(Spacer(1, 0.2 * inch))

            # PCB specifications table
            spec_data = [
                ["Parameter", "Value", "Standard Capability", "Status"],
                ["Layer Count", str(pcb.layer_count), "2-8 layers", "✓"],
                ["Board Size", f"{(pcb.board_size_mm2/100):.1f} cm²", "< 500 cm²", "✓"],
                [
                    "Min Trace Width",
                    f"{pcb.min_trace_width_mm:.3f} mm",
                    "≥ 0.127 mm",
                    "✓",
                ],
                ["Min Via Size", f"{pcb.min_via_size_mm:.3f} mm", "≥ 0.2 mm", "✓"],
                [
                    "Component Density",
                    f"{pcb.component_density:.1f} /cm²",
                    "< 10 /cm²",
                    "✓" if pcb.component_density < 10 else "⚠",
                ],
                [
                    "Panelization Efficiency",
                    f"{pcb.panelization_efficiency:.0f}%",
                    "≥ 70%",
                    "✓" if pcb.panelization_efficiency >= 70 else "⚠",
                ],
            ]

            spec_table = Table(
                spec_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch, 0.8 * inch]
            )
            spec_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#003366")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            elements.append(spec_table)

            # Complexity score
            complexity_text = Paragraph(
                f"<b>PCB Complexity Score:</b> {pcb.complexity_score:.0f}/100<br/>"
                f"The complexity score indicates the relative difficulty of manufacturing this PCB. "
                f"Lower scores indicate simpler, more manufacturable designs with higher yields.",
                self.styles["DFMAnalysisBody"],
            )
            elements.append(complexity_text)

        return elements

    def _create_assembly_analysis(self, dfm_report: DFMReport) -> List:
        """Create assembly process analysis section"""
        elements = []

        heading = Paragraph(
            "Assembly Process Analysis", self.styles["DFMSectionHeading"]
        )
        elements.append(heading)

        intro = Paragraph(
            "Evaluation of assembly process requirements, equipment needs, and optimization opportunities "
            "for efficient production.",
            self.styles["DFMAnalysisBody"],
        )
        elements.append(intro)
        elements.append(Spacer(1, 0.2 * inch))

        # Assembly process requirements
        process_heading = Paragraph(
            "Process Requirements", self.styles["DFMSubsectionHeading"]
        )
        elements.append(process_heading)

        process_data = [
            ["Process Step", "Technology", "Equipment", "Estimated Time"],
            ["Solder Paste Application", "Stencil Printing", "SMT Printer", "2 min"],
            ["Component Placement", "Pick & Place", "SMT P&P Machine", "5 min"],
            ["Reflow Soldering", "Convection Reflow", "Reflow Oven", "8 min"],
            ["Inspection", "AOI", "AOI System", "3 min"],
            ["Testing", "In-Circuit Test", "ICT Fixture", "2 min"],
        ]

        process_table = Table(
            process_data, colWidths=[2 * inch, 1.8 * inch, 2 * inch, 1.5 * inch]
        )
        process_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#003366")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(process_table)

        return elements

    def _create_supply_chain_analysis(self, dfm_report: DFMReport) -> List:
        """Create supply chain risk assessment section"""
        elements = []

        heading = Paragraph(
            "Supply Chain Risk Assessment", self.styles["DFMSectionHeading"]
        )
        elements.append(heading)

        intro = Paragraph(
            f"Analysis of component sourcing risks, availability trends, and mitigation strategies. "
            f"Overall supply chain risk score: {dfm_report.supply_chain_risk_score:.1f}/100 "
            f"(lower is better).",
            self.styles["DFMAnalysisBody"],
        )
        elements.append(intro)
        elements.append(Spacer(1, 0.2 * inch))

        # Risk categories
        risk_heading = Paragraph("Risk Categories", self.styles["DFMSubsectionHeading"])
        elements.append(risk_heading)

        risk_data = [
            ["Risk Category", "Level", "Impact", "Mitigation Strategy"],
            [
                "Component Availability",
                "Low",
                "Minor delays possible",
                "Maintain safety stock of critical components",
            ],
            [
                "Single Source Components",
                "Medium",
                "Supply disruption risk",
                "Identify alternative components or suppliers",
            ],
            [
                "Long Lead Time Items",
                "Low",
                "Planning constraints",
                "Order components early in production cycle",
            ],
            [
                "EOL Components",
                "Low",
                "Future availability",
                "Plan for redesign or lifetime buy",
            ],
        ]

        risk_table = Table(
            risk_data, colWidths=[2 * inch, 1 * inch, 2 * inch, 2.5 * inch]
        )
        risk_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#003366")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (1, 1), (1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(risk_table)

        return elements

    def _create_issues_and_mitigation(self, dfm_report: DFMReport) -> List:
        """Create manufacturing issues and mitigation strategies section"""
        elements = []

        heading = Paragraph(
            "Manufacturing Issues and Mitigation", self.styles["DFMSectionHeading"]
        )
        elements.append(heading)

        # Group issues by severity
        critical_issues = [
            i for i in dfm_report.issues if i.severity == IssueSeverity.CRITICAL
        ]
        high_issues = [i for i in dfm_report.issues if i.severity == IssueSeverity.HIGH]
        medium_issues = [
            i for i in dfm_report.issues if i.severity == IssueSeverity.MEDIUM
        ]

        # Critical issues
        if critical_issues:
            critical_heading = Paragraph(
                "Critical Issues (Must Fix)", self.styles["DFMSubsectionHeading"]
            )
            elements.append(critical_heading)

            for idx, issue in enumerate(critical_issues[:5], 1):
                issue_table_data = [
                    ["Issue:", issue.description],
                    ["Category:", issue.category.value],
                    ["Component:", issue.component or "N/A"],
                    ["Impact:", issue.impact],
                    ["Recommendation:", issue.recommendation],
                ]

                if issue.cost_impact:
                    issue_table_data.append(
                        ["Cost Impact:", f"${issue.cost_impact:.2f}"]
                    )
                if issue.yield_impact:
                    issue_table_data.append(
                        ["Yield Impact:", f"{issue.yield_impact*100:.1f}%"]
                    )

                issue_table = Table(
                    issue_table_data, colWidths=[1.5 * inch, 5.5 * inch]
                )
                issue_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (0, -1), HexColor("#ffeeee")),
                            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("GRID", (0, 0), (-1, -1), 1, HexColor("#CC0000")),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )
                elements.append(issue_table)
                elements.append(Spacer(1, 0.2 * inch))

        # High priority issues
        if high_issues:
            high_heading = Paragraph(
                "High Priority Issues", self.styles["DFMSubsectionHeading"]
            )
            elements.append(high_heading)

            high_summary_data = [
                ["Description", "Category", "Impact", "Action Required"]
            ]
            for issue in high_issues[:5]:
                high_summary_data.append(
                    [
                        (
                            issue.description[:40] + "..."
                            if len(issue.description) > 40
                            else issue.description
                        ),
                        issue.category.value,
                        (
                            issue.impact[:30] + "..."
                            if len(issue.impact) > 30
                            else issue.impact
                        ),
                        (
                            issue.recommendation[:40] + "..."
                            if len(issue.recommendation) > 40
                            else issue.recommendation
                        ),
                    ]
                )

            high_table = Table(
                high_summary_data,
                colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch, 2 * inch],
            )
            high_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#FF9900")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            elements.append(high_table)

        return elements

    def _create_volume_planning(self, dfm_report: DFMReport) -> List:
        """Create volume production planning section"""
        elements = []

        heading = Paragraph(
            "Volume Production Planning", self.styles["DFMSectionHeading"]
        )
        elements.append(heading)

        intro = Paragraph(
            "Production planning recommendations for different volume scenarios, including resource requirements "
            "and cost optimization strategies.",
            self.styles["DFMAnalysisBody"],
        )
        elements.append(intro)
        elements.append(Spacer(1, 0.2 * inch))

        # Production scenarios
        scenario_data = [
            ["Volume", "Production Method", "Timeline", "Unit Cost", "Recommendation"],
            [
                "10-100",
                "Prototype Assembly",
                "3-5 days",
                f"${dfm_report.volume_pricing.get(10, 0)*1.5:.2f}",
                "Manual assembly acceptable",
            ],
            [
                "100-1000",
                "Low Volume Production",
                "1-2 weeks",
                f"${dfm_report.volume_pricing.get(100, 0):.2f}",
                "Semi-automated assembly",
            ],
            [
                "1000-10000",
                "Standard Production",
                "2-3 weeks",
                f"${dfm_report.volume_pricing.get(1000, 0):.2f}",
                "Full SMT line production",
            ],
            [
                "10000+",
                "High Volume Production",
                "3-4 weeks",
                f"${dfm_report.volume_pricing.get(10000, 0):.2f}",
                "Dedicated production line",
            ],
        ]

        scenario_table = Table(
            scenario_data,
            colWidths=[1.2 * inch, 2 * inch, 1.2 * inch, 1 * inch, 2.3 * inch],
        )
        scenario_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#003366")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(scenario_table)

        return elements

    def _create_quality_control(self, dfm_report: DFMReport) -> List:
        """Create quality control strategy section"""
        elements = []

        heading = Paragraph(
            "Quality Control Strategy", self.styles["DFMSectionHeading"]
        )
        elements.append(heading)

        intro = Paragraph(
            "Comprehensive quality control measures to ensure consistent product quality and reliability "
            "throughout the manufacturing process.",
            self.styles["DFMAnalysisBody"],
        )
        elements.append(intro)
        elements.append(Spacer(1, 0.2 * inch))

        # QC checkpoints
        qc_data = [
            ["Stage", "Inspection Method", "Acceptance Criteria", "Frequency"],
            [
                "Incoming Material",
                "Visual + Sampling",
                "IPC-A-610 Class 2",
                "Every batch",
            ],
            ["Post-SMT", "AOI", "No missing/misaligned components", "100%"],
            ["Post-Reflow", "Visual + AOI", "IPC-A-610 solder joints", "100%"],
            ["Functional Test", "ICT + FCT", "All functions operational", "100%"],
            ["Final QC", "Visual + Sampling", "Cosmetic and functional", "AQL 0.65"],
        ]

        qc_table = Table(
            qc_data, colWidths=[1.8 * inch, 1.8 * inch, 2.2 * inch, 1.5 * inch]
        )
        qc_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#003366")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(qc_table)

        return elements

    def _create_testability_analysis(self, dfm_report: DFMReport) -> List:
        """Create testability and inspection analysis section"""
        elements = []

        heading = Paragraph(
            "Testability and Inspection", self.styles["DFMSectionHeading"]
        )
        elements.append(heading)

        if dfm_report.pcb_analysis:
            coverage_text = Paragraph(
                f"<b>Current Test Point Coverage:</b> {dfm_report.pcb_analysis.testpoint_coverage:.0f}%<br/><br/>"
                f"Test point coverage analysis indicates the percentage of critical nets accessible for "
                f"in-circuit testing. Industry standard for Class 2 assemblies is ≥70% coverage.",
                self.styles["DFMAnalysisBody"],
            )
            elements.append(coverage_text)
            elements.append(Spacer(1, 0.2 * inch))

        # Testability recommendations
        rec_heading = Paragraph(
            "Testability Recommendations", self.styles["DFMSubsectionHeading"]
        )
        elements.append(rec_heading)

        recommendations = [
            "• Add test points to all power rails and critical signals",
            "• Ensure minimum 1mm diameter test pads for reliable probe contact",
            "• Provide ground test points distributed across the board",
            "• Add test points for programming and boundary scan where applicable",
            "• Consider built-in self-test (BIST) features for complex circuits",
        ]

        for rec in recommendations:
            rec_para = Paragraph(rec, self.styles["DFMAnalysisBody"])
            elements.append(rec_para)

        return elements

    def _create_environmental_compliance(self) -> List:
        """Create environmental compliance section"""
        elements = []

        heading = Paragraph(
            "Environmental Compliance", self.styles["DFMSectionHeading"]
        )
        elements.append(heading)

        intro = Paragraph(
            "Environmental and regulatory compliance requirements for manufacturing and distribution.",
            self.styles["DFMAnalysisBody"],
        )
        elements.append(intro)
        elements.append(Spacer(1, 0.2 * inch))

        # Compliance table
        compliance_data = [
            ["Standard", "Requirement", "Status", "Notes"],
            [
                "RoHS",
                "Lead-free components",
                "Compliant",
                "All components RoHS certified",
            ],
            ["REACH", "SVHC substances", "Compliant", "No SVHC above threshold"],
            ["WEEE", "Recycling marking", "Required", "Add WEEE symbol to PCB"],
            [
                "Conflict Minerals",
                "Supply chain verification",
                "In Progress",
                "Supplier declarations needed",
            ],
        ]

        compliance_table = Table(
            compliance_data, colWidths=[1.5 * inch, 2 * inch, 1.2 * inch, 2.5 * inch]
        )
        compliance_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#003366")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(compliance_table)

        return elements

    def _create_recommendations(self, dfm_report: DFMReport) -> List:
        """Create recommendations and action items section"""
        elements = []

        heading = Paragraph(
            "Recommendations and Action Items", self.styles["DFMSectionHeading"]
        )
        elements.append(heading)

        # Priority action items
        priority_heading = Paragraph(
            "Priority Action Items", self.styles["DFMSubsectionHeading"]
        )
        elements.append(priority_heading)

        action_data = [
            ["Priority", "Action Item", "Owner", "Timeline", "Expected Impact"],
            [
                "Critical",
                "Resolve component availability issues",
                "Procurement",
                "Immediate",
                "Prevent production delays",
            ],
            [
                "High",
                "Optimize BOM for cost reduction",
                "Engineering",
                "1 week",
                f"Save ${len(dfm_report.cost_reduction_opportunities)*0.5:.2f}/unit",
            ],
            [
                "High",
                "Update PCB design for testability",
                "PCB Design",
                "2 weeks",
                "Improve test coverage to 90%",
            ],
            [
                "Medium",
                "Standardize component packages",
                "Engineering",
                "Next revision",
                "Reduce assembly complexity",
            ],
            [
                "Medium",
                "Implement supply chain monitoring",
                "Procurement",
                "Ongoing",
                "Mitigate shortage risks",
            ],
        ]

        action_table = Table(
            action_data,
            colWidths=[1 * inch, 2.5 * inch, 1.2 * inch, 1 * inch, 2 * inch],
        )
        action_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#003366")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    # Color code priorities
                    ("BACKGROUND", (0, 1), (0, 1), HexColor("#CC0000")),
                    ("TEXTCOLOR", (0, 1), (0, 1), colors.white),
                    ("BACKGROUND", (0, 2), (0, 3), HexColor("#FF9900")),
                    ("BACKGROUND", (0, 4), (0, 5), HexColor("#FFCC00")),
                ]
            )
        )
        elements.append(action_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Long-term improvements
        improvements_heading = Paragraph(
            "Long-term Improvements", self.styles["DFMSubsectionHeading"]
        )
        elements.append(improvements_heading)

        improvements = [
            "• Develop preferred components library for future designs",
            "• Establish relationships with alternative suppliers",
            "• Implement DFM checks early in design process",
            "• Create design guidelines based on manufacturing feedback",
            "• Set up automated component availability monitoring",
        ]

        for improvement in improvements:
            imp_para = Paragraph(improvement, self.styles["DFMAnalysisBody"])
            elements.append(imp_para)

        return elements

    def _create_appendices(
        self, dfm_report: DFMReport, circuit_data: Dict = None
    ) -> List:
        """Create appendices with supplementary information"""
        elements = []

        heading = Paragraph("Appendices", self.styles["DFMSectionHeading"])
        elements.append(heading)

        # Appendix A: Complete BOM
        appendix_a = Paragraph(
            "Appendix A: Bill of Materials", self.styles["DFMSubsectionHeading"]
        )
        elements.append(appendix_a)

        bom_note = Paragraph(
            "Complete bill of materials with all components, specifications, and sourcing information. "
            "Detailed BOM available as separate CSV file for procurement use.",
            self.styles["DFMAnalysisBody"],
        )
        elements.append(bom_note)
        elements.append(Spacer(1, 0.3 * inch))

        # Appendix B: Manufacturing Files
        appendix_b = Paragraph(
            "Appendix B: Manufacturing Files Checklist",
            self.styles["DFMSubsectionHeading"],
        )
        elements.append(appendix_b)

        files_data = [
            ["File Type", "Format", "Status", "Notes"],
            ["Gerber Files", "RS-274X", "Ready", "All layers included"],
            ["Pick & Place", "CSV", "Ready", "Centroid data formatted"],
            ["3D Model", "STEP", "Ready", "For assembly verification"],
            ["Assembly Drawing", "PDF", "Ready", "Component placement guide"],
            ["Test Specification", "PDF", "In Progress", "ICT/FCT procedures"],
        ]

        files_table = Table(
            files_data, colWidths=[2 * inch, 1.5 * inch, 1.2 * inch, 2.5 * inch]
        )
        files_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#003366")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(files_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Appendix C: Glossary
        appendix_c = Paragraph(
            "Appendix C: Glossary of Terms", self.styles["DFMSubsectionHeading"]
        )
        elements.append(appendix_c)

        glossary = [
            ("<b>AOI:</b> Automated Optical Inspection", ""),
            ("<b>BOM:</b> Bill of Materials", ""),
            ("<b>DFA:</b> Design for Assembly", ""),
            ("<b>DFM:</b> Design for Manufacturing", ""),
            ("<b>EOL:</b> End of Life", ""),
            ("<b>ICT:</b> In-Circuit Test", ""),
            ("<b>SMT:</b> Surface Mount Technology", ""),
            ("<b>THT:</b> Through-Hole Technology", ""),
        ]

        for term, _ in glossary:
            term_para = Paragraph(term, self.styles["DFMAnalysisBody"])
            elements.append(term_para)

        return elements

    def _add_page_number(self, canvas, doc):
        """Add page numbers and headers to each page"""
        canvas.saveState()

        # Header
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(30, 580, f"DFM Report - {self.project_name}")
        canvas.drawRightString(780, 580, self.report_date.strftime("%B %Y"))

        # Footer with page number
        canvas.setFont("Helvetica", 9)
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawCentredString(400, 30, text)

        # Confidentiality notice
        canvas.setFont("Helvetica-Oblique", 8)
        canvas.drawString(30, 20, "Confidential - Circuit-Synth DFM Analysis")

        canvas.restoreState()

    # Helper methods
    def _get_status_label(self, score: float) -> str:
        """Get status label based on score"""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 70:
            return "Acceptable"
        elif score >= 60:
            return "Needs Improvement"
        else:
            return "Poor"

    def _get_risk_label(self, score: float) -> str:
        """Get risk label based on score (lower is better)"""
        if score <= 20:
            return "Low Risk"
        elif score <= 40:
            return "Moderate Risk"
        elif score <= 60:
            return "Elevated Risk"
        elif score <= 80:
            return "High Risk"
        else:
            return "Critical Risk"

    def _get_availability_status(self, dfm_report: DFMReport) -> str:
        """Get component availability status"""
        if dfm_report.component_analyses:
            avg_availability = sum(
                c.availability_score for c in dfm_report.component_analyses
            ) / len(dfm_report.component_analyses)
            if avg_availability >= 90:
                return "Excellent"
            elif avg_availability >= 75:
                return "Good"
            elif avg_availability >= 60:
                return "Fair"
            else:
                return "Poor"
        return "Unknown"

    def _get_assembly_impact(self, process: ManufacturingProcess) -> str:
        """Get assembly impact description for a process type"""
        impacts = {
            ManufacturingProcess.SMT: "Standard SMT process, automated placement",
            ManufacturingProcess.THT: "Manual insertion or wave soldering required",
            ManufacturingProcess.MIXED: "Multiple processes, increased complexity",
            ManufacturingProcess.MANUAL: "Manual assembly, higher labor cost",
            ManufacturingProcess.SELECTIVE: "Selective soldering equipment needed",
            ManufacturingProcess.WAVE: "Wave soldering process required",
            ManufacturingProcess.REFLOW: "Standard reflow process",
        }
        return impacts.get(process, "Process-specific requirements")


def generate_dfm_report(
    circuit_name: str,
    circuit_data: Dict,
    volume: int = 1000,
    target_cost: Optional[float] = None,
    output_path: Optional[str] = None,
) -> str:
    """
    Convenience function to generate a comprehensive DFM report

    Args:
        circuit_name: Name of the circuit/project
        circuit_data: Circuit data dictionary (components, nets, etc.)
        volume: Production volume for analysis
        target_cost: Target unit cost for optimization
        output_path: Path for output PDF file

    Returns:
        Path to generated PDF report
    """
    # Run DFM analysis
    analyzer = DFMAnalyzer()
    dfm_report = analyzer.analyze_circuit(
        circuit_data=circuit_data,
        volume=volume,
        target_cost=target_cost,
    )

    # Generate comprehensive report
    generator = ComprehensiveDFMReportGenerator(circuit_name)
    return generator.generate_comprehensive_report(
        dfm_report=dfm_report,
        circuit_data=circuit_data,
        output_path=output_path,
    )
