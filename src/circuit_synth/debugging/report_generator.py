"""
PDF Report Generator for Circuit Debugging Sessions

Generates professional PDF reports from debugging sessions with
charts, tables, and formatted analysis.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.platypus import (
        Flowable,
        Image,
        KeepTogether,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.platypus.tableofcontents import TableOfContents

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not installed. PDF generation disabled.")
    print("Install with: pip install reportlab")


class DebugReportGenerator:
    """Generates professional PDF reports from debugging sessions"""

    def __init__(self, session_data: Dict[str, Any]):
        """Initialize with session data"""
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "reportlab is required for PDF generation. Install with: pip install reportlab"
            )

        self.session = session_data
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Title"],
                fontSize=24,
                textColor=colors.HexColor("#1a1a1a"),
                spaceAfter=30,
                alignment=TA_CENTER,
            )
        )

        # Heading styles
        self.styles.add(
            ParagraphStyle(
                name="CustomHeading1",
                parent=self.styles["Heading1"],
                fontSize=18,
                textColor=colors.HexColor("#2c3e50"),
                spaceBefore=20,
                spaceAfter=12,
                leftIndent=0,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="CustomHeading2",
                parent=self.styles["Heading2"],
                fontSize=14,
                textColor=colors.HexColor("#34495e"),
                spaceBefore=15,
                spaceAfter=10,
                leftIndent=10,
            )
        )

        # Body text
        self.styles.add(
            ParagraphStyle(
                name="CustomBody",
                parent=self.styles["BodyText"],
                fontSize=11,
                textColor=colors.HexColor("#2c3e50"),
                alignment=TA_JUSTIFY,
                spaceBefore=6,
                spaceAfter=6,
            )
        )

        # Table header
        self.styles.add(
            ParagraphStyle(
                name="TableHeader",
                parent=self.styles["BodyText"],
                fontSize=11,
                textColor=colors.white,
                alignment=TA_CENTER,
                bold=True,
            )
        )

    def generate_pdf(self, output_path: str = "debug_report.pdf") -> str:
        """Generate PDF report"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        # Build content
        story = []

        # Title page
        story.extend(self._create_title_page())
        story.append(PageBreak())

        # Executive summary
        story.extend(self._create_executive_summary())
        story.append(PageBreak())

        # Symptoms and measurements
        story.extend(self._create_symptoms_section())
        story.append(Spacer(1, 0.3 * inch))
        story.extend(self._create_measurements_section())
        story.append(PageBreak())

        # Issue analysis
        story.extend(self._create_issues_section())
        story.append(PageBreak())

        # Resolution
        story.extend(self._create_resolution_section())
        story.append(PageBreak())

        # Recommendations
        story.extend(self._create_recommendations_section())

        # Build PDF
        doc.build(story)

        return output_path

    def _create_title_page(self) -> List[Flowable]:
        """Create title page"""
        elements = []

        # Title
        elements.append(Spacer(1, 2 * inch))
        elements.append(Paragraph("PCB Debugging Report", self.styles["CustomTitle"]))

        elements.append(Spacer(1, 0.5 * inch))

        # Session info
        info_data = [
            [
                "Board:",
                f"{self.session.get('board_name', 'Unknown')} {self.session.get('board_version', '')}",
            ],
            ["Session ID:", self.session.get("session_id", "N/A")[:8] + "..."],
            ["Date:", self.session.get("started_at", "Unknown")],
            [
                "Status:",
                "Resolved" if self.session.get("resolution") else "In Progress",
            ],
        ]

        info_table = Table(info_data, colWidths=[2 * inch, 3 * inch])
        info_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 12),
                    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                    ("ALIGN", (1, 0), (1, -1), "LEFT"),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#2c3e50")),
                ]
            )
        )

        elements.append(info_table)

        return elements

    def _create_executive_summary(self) -> List[Flowable]:
        """Create executive summary section"""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles["CustomHeading1"]))

        # Summary text
        root_cause = self.session.get("root_cause", "Under investigation")
        resolution = self.session.get("resolution", "In progress")

        summary_text = f"""
        The debugging session for {self.session.get('board_name', 'the board')} identified and resolved
        critical issues affecting board functionality. The root cause was determined to be: {root_cause}.
        The issue was resolved by: {resolution}.
        """

        elements.append(Paragraph(summary_text, self.styles["CustomBody"]))
        elements.append(Spacer(1, 0.2 * inch))

        # Key metrics
        symptoms_count = len(self.session.get("symptoms", []))
        measurements_count = len(self.session.get("measurements", {}))
        issues_count = len(self.session.get("identified_issues", []))

        metrics_data = [
            ["Symptoms Reported:", str(symptoms_count)],
            ["Measurements Taken:", str(measurements_count)],
            ["Issues Identified:", str(issues_count)],
            [
                "Resolution Status:",
                "Complete" if self.session.get("resolution") else "Ongoing",
            ],
        ]

        metrics_table = Table(metrics_data, colWidths=[2.5 * inch, 2 * inch])
        metrics_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ecf0f1")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#bdc3c7")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        elements.append(metrics_table)

        return elements

    def _create_symptoms_section(self) -> List[Flowable]:
        """Create symptoms section"""
        elements = []

        elements.append(Paragraph("Reported Symptoms", self.styles["CustomHeading1"]))

        symptoms = self.session.get("symptoms", [])
        if symptoms:
            for symptom in symptoms:
                bullet = Paragraph(f"• {symptom}", self.styles["CustomBody"])
                elements.append(bullet)
        else:
            elements.append(
                Paragraph("No symptoms reported", self.styles["CustomBody"])
            )

        return elements

    def _create_measurements_section(self) -> List[Flowable]:
        """Create measurements table"""
        elements = []

        elements.append(Paragraph("Test Measurements", self.styles["CustomHeading1"]))

        measurements = self.session.get("measurements", {})
        if measurements:
            # Create table data
            table_data = [["Test Point", "Value", "Unit", "Notes"]]

            for name, data in measurements.items():
                table_data.append(
                    [
                        name,
                        str(data.get("value", "")),
                        data.get("unit", ""),
                        (
                            data.get("notes", "")[:30] + "..."
                            if len(data.get("notes", "")) > 30
                            else data.get("notes", "")
                        ),
                    ]
                )

            # Create table
            table = Table(
                table_data, colWidths=[2 * inch, 1 * inch, 0.7 * inch, 2.8 * inch]
            )
            table.setStyle(
                TableStyle(
                    [
                        # Header row
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3498db")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        # Data rows
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#bdc3c7")),
                        ("ALIGN", (1, 1), (2, -1), "CENTER"),
                        # Alternating row colors
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.HexColor("#ecf0f1")],
                        ),
                        # Padding
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )

            elements.append(table)
        else:
            elements.append(
                Paragraph("No measurements recorded", self.styles["CustomBody"])
            )

        return elements

    def _create_issues_section(self) -> List[Flowable]:
        """Create issues analysis section"""
        elements = []

        elements.append(Paragraph("Issue Analysis", self.styles["CustomHeading1"]))

        issues = self.session.get("identified_issues", [])

        for i, issue in enumerate(issues, 1):
            # Issue title with severity
            severity = issue.get("severity", "unknown").upper()
            severity_color = {
                "CRITICAL": colors.red,
                "HIGH": colors.orange,
                "MEDIUM": colors.yellow,
                "LOW": colors.green,
            }.get(severity, colors.grey)

            issue_title = f"Issue {i}: {issue.get('title', 'Unknown Issue')}"
            elements.append(Paragraph(issue_title, self.styles["CustomHeading2"]))

            # Issue details table
            details_data = [
                ["Severity:", severity],
                ["Category:", issue.get("category", "Unknown")],
                ["Confidence:", f"{issue.get('confidence', 0)*100:.0f}%"],
            ]

            details_table = Table(details_data, colWidths=[1.5 * inch, 3 * inch])
            details_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("TEXTCOLOR", (1, 0), (1, 0), severity_color),
                    ]
                )
            )

            elements.append(details_table)
            elements.append(Spacer(1, 0.1 * inch))

            # Description
            elements.append(
                Paragraph(
                    issue.get("description", "No description available"),
                    self.styles["CustomBody"],
                )
            )

            # Probable causes
            if issue.get("probable_causes"):
                elements.append(Paragraph("Probable Causes:", self.styles["BodyText"]))
                for cause in issue["probable_causes"][:3]:
                    elements.append(Paragraph(f"• {cause}", self.styles["CustomBody"]))

            # Test suggestions
            if issue.get("test_suggestions"):
                elements.append(
                    Paragraph("Recommended Tests:", self.styles["BodyText"])
                )
                for test in issue["test_suggestions"][:3]:
                    elements.append(Paragraph(f"• {test}", self.styles["CustomBody"]))

            elements.append(Spacer(1, 0.2 * inch))

        if not issues:
            elements.append(
                Paragraph("No issues identified", self.styles["CustomBody"])
            )

        return elements

    def _create_resolution_section(self) -> List[Flowable]:
        """Create resolution section"""
        elements = []

        elements.append(Paragraph("Resolution", self.styles["CustomHeading1"]))

        if self.session.get("resolution"):
            elements.append(
                Paragraph(
                    f"<b>Root Cause:</b> {self.session.get('root_cause', 'Not specified')}",
                    self.styles["CustomBody"],
                )
            )

            elements.append(
                Paragraph(
                    f"<b>Resolution:</b> {self.session.get('resolution', 'Not specified')}",
                    self.styles["CustomBody"],
                )
            )

            # Observations
            observations = self.session.get("observations", [])
            if observations:
                elements.append(Spacer(1, 0.1 * inch))
                elements.append(Paragraph("Observations:", self.styles["BodyText"]))
                for obs in observations:
                    if isinstance(obs, dict):
                        text = obs.get("text", str(obs))
                    else:
                        text = str(obs)
                    elements.append(Paragraph(f"• {text}", self.styles["CustomBody"]))
        else:
            elements.append(
                Paragraph("Session still in progress", self.styles["CustomBody"])
            )

        return elements

    def _create_recommendations_section(self) -> List[Flowable]:
        """Create recommendations section"""
        elements = []

        elements.append(Paragraph("Recommendations", self.styles["CustomHeading1"]))

        recommendations = [
            "Implement regular testing procedures for critical components",
            "Add protection circuits to prevent similar failures",
            "Document this failure mode in the knowledge base",
            "Consider design review for vulnerable components",
            "Update manufacturing test procedures",
        ]

        elements.append(Paragraph("Preventive Measures:", self.styles["BodyText"]))
        for rec in recommendations:
            elements.append(Paragraph(f"• {rec}", self.styles["CustomBody"]))

        return elements


def generate_pdf_from_session(
    session_file: str, output_file: str = "debug_report.pdf"
) -> str:
    """Generate PDF from session JSON file"""
    with open(session_file, "r") as f:
        session_data = json.load(f)

    generator = DebugReportGenerator(session_data)
    return generator.generate_pdf(output_file)
