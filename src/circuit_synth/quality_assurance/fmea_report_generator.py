#!/usr/bin/env python3
"""
FMEA PDF Report Generator for Circuit-Synth
Generates professional PDF reports for circuit board failure analysis
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# PDF generation libraries
try:
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        HRFlowable,
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
    print("Warning: reportlab not installed. Install with: pip install reportlab")

# Alternative: markdown to PDF using weasyprint
try:
    import markdown
    import weasyprint

    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


class FMEAReportGenerator:
    """Generates professional PDF FMEA reports for circuit boards"""

    def __init__(self, project_name: str, author: str = "Circuit-Synth FMEA Analyzer"):
        self.project_name = project_name
        self.author = author
        self.report_date = datetime.now().strftime("%Y-%m-%d")
        self.styles = getSampleStyleSheet() if REPORTLAB_AVAILABLE else None
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom styles for the PDF report"""
        if not REPORTLAB_AVAILABLE:
            return

        # Title style
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Title"],
                fontSize=24,
                textColor=HexColor("#2E3F4F"),
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
                textColor=HexColor("#2E3F4F"),
                spaceAfter=12,
                spaceBefore=12,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="CustomHeading2",
                parent=self.styles["Heading2"],
                fontSize=14,
                textColor=HexColor("#2E3F4F"),
                spaceAfter=6,
                spaceBefore=12,
            )
        )

        # Body text style
        self.styles.add(
            ParagraphStyle(
                name="CustomBody",
                parent=self.styles["BodyText"],
                fontSize=10,
                alignment=TA_JUSTIFY,
                spaceAfter=12,
            )
        )

    def generate_fmea_report(
        self, circuit_data: Dict, failure_modes: List[Dict], output_path: str = None
    ) -> str:
        """
        Generate a complete FMEA PDF report

        Args:
            circuit_data: Dictionary containing circuit information
            failure_modes: List of failure mode dictionaries with RPN data
            output_path: Optional output path for the PDF

        Returns:
            Path to the generated PDF file
        """
        if not REPORTLAB_AVAILABLE:
            print("Error: reportlab is required for PDF generation")
            print("Install with: pip install reportlab")
            return None

        if output_path is None:
            output_path = f"{self.project_name}_FMEA_Report_{self.report_date}.pdf"

        # Create the PDF document in landscape orientation for better table visibility
        from reportlab.lib.pagesizes import landscape

        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(letter),
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        # Build the content
        story = []

        # Title Page
        story.extend(self._create_title_page())
        story.append(PageBreak())

        # Executive Summary
        story.extend(self._create_executive_summary(circuit_data, failure_modes))
        story.append(PageBreak())

        # System Overview
        story.extend(self._create_system_overview(circuit_data))
        story.append(PageBreak())

        # FMEA Analysis Table
        story.extend(self._create_fmea_table(failure_modes))
        story.append(PageBreak())

        # Risk Matrix
        story.extend(self._create_risk_matrix(failure_modes))
        story.append(PageBreak())

        # Recommendations
        story.extend(self._create_recommendations(failure_modes))

        # Build the PDF
        doc.build(story)

        print(f"✅ FMEA Report generated: {output_path}")
        return output_path

    def _create_title_page(self) -> List:
        """Create the title page"""
        elements = []

        # Add spacing
        elements.append(Spacer(1, 2 * inch))

        # Title
        title = Paragraph(
            f"FMEA Analysis Report<br/>{self.project_name}", self.styles["CustomTitle"]
        )
        elements.append(title)

        elements.append(Spacer(1, 0.5 * inch))

        # Subtitle
        subtitle = Paragraph(
            "Failure Mode and Effects Analysis<br/>for Electronic Circuit Board",
            self.styles["CustomHeading2"],
        )
        elements.append(subtitle)

        elements.append(Spacer(1, 2 * inch))

        # Report info
        info_data = [
            ["Report Date:", self.report_date],
            ["Prepared by:", self.author],
            ["Standard:", "AIAG-VDA FMEA / IPC-A-610"],
            ["Classification:", "Quality Assurance Document"],
        ]

        info_table = Table(info_data, colWidths=[2 * inch, 3 * inch])
        info_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )
        elements.append(info_table)

        return elements

    def _create_executive_summary(
        self, circuit_data: Dict, failure_modes: List[Dict]
    ) -> List:
        """Create executive summary section"""
        elements = []

        # Heading
        elements.append(Paragraph("Executive Summary", self.styles["CustomHeading1"]))
        elements.append(Spacer(1, 0.2 * inch))

        # Calculate statistics
        total_modes = len(failure_modes)
        critical_modes = sum(1 for fm in failure_modes if fm.get("rpn", 0) >= 300)
        high_risk_modes = sum(
            1 for fm in failure_modes if 125 <= fm.get("rpn", 0) < 300
        )
        avg_rpn = (
            sum(fm.get("rpn", 0) for fm in failure_modes) / total_modes
            if total_modes > 0
            else 0
        )

        # Summary text
        summary_text = f"""
        This FMEA analysis evaluates the {self.project_name} circuit design to identify 
        potential failure modes and assess associated risks. The analysis examined 
        {circuit_data.get('component_count', 'N/A')} components across 
        {circuit_data.get('subsystem_count', 'N/A')} subsystems.
        """
        elements.append(Paragraph(summary_text, self.styles["CustomBody"]))

        # Key findings table
        elements.append(Paragraph("Key Findings", self.styles["CustomHeading2"]))

        findings_data = [
            ["Metric", "Value", "Status"],
            [
                "Total Failure Modes Analyzed",
                str(total_modes),
                self._get_status_indicator(total_modes > 10),
            ],
            [
                "Critical Risk Modes (RPN ≥ 300)",
                str(critical_modes),
                self._get_status_indicator(critical_modes == 0),
            ],
            [
                "High Risk Modes (125 ≤ RPN < 300)",
                str(high_risk_modes),
                self._get_status_indicator(high_risk_modes <= 3),
            ],
            [
                "Average RPN Score",
                f"{avg_rpn:.1f}",
                self._get_status_indicator(avg_rpn < 150),
            ],
        ]

        findings_table = Table(
            findings_data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch]
        )
        findings_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.lightgrey],
                    ),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(findings_table)

        return elements

    def _create_system_overview(self, circuit_data: Dict) -> List:
        """Create system overview section"""
        elements = []

        elements.append(Paragraph("System Overview", self.styles["CustomHeading1"]))
        elements.append(Spacer(1, 0.1 * inch))

        # Circuit description
        description = circuit_data.get("description", "No description provided")
        elements.append(Paragraph(description, self.styles["CustomBody"]))

        # Subsystems
        if "subsystems" in circuit_data:
            elements.append(Paragraph("Subsystems", self.styles["CustomHeading2"]))
            for subsystem in circuit_data["subsystems"]:
                bullet = (
                    f"• <b>{subsystem['name']}</b>: {subsystem.get('description', '')}"
                )
                elements.append(Paragraph(bullet, self.styles["CustomBody"]))

        return elements

    def _create_fmea_table(self, failure_modes: List[Dict]) -> List:
        """Create the main FMEA analysis table"""
        elements = []

        elements.append(Paragraph("FMEA Analysis Table", self.styles["CustomHeading1"]))
        elements.append(Spacer(1, 0.1 * inch))

        # Split into multiple tables if too many failure modes
        # Show top 15 most critical in main table
        critical_modes = sorted(
            failure_modes, key=lambda x: x.get("rpn", 0), reverse=True
        )[:15]

        # Table headers with better formatting
        headers = ["#", "Component", "Failure Mode", "S", "O", "D", "RPN", "Risk"]

        # Prepare table data with Paragraph objects for text wrapping
        table_data = [headers]
        for i, fm in enumerate(critical_modes, 1):
            risk_level = self._get_risk_level(fm.get("rpn", 0))

            # Use Paragraph for long text fields to enable wrapping
            component_para = Paragraph(fm.get("component", ""), self.styles["BodyText"])
            failure_para = Paragraph(
                fm.get("failure_mode", ""), self.styles["BodyText"]
            )

            row = [
                str(i),
                component_para,
                failure_para,
                str(fm.get("severity", 0)),
                str(fm.get("occurrence", 0)),
                str(fm.get("detection", 0)),
                str(fm.get("rpn", 0)),
                risk_level,
            ]
            table_data.append(row)

        # Create table with better column widths for landscape orientation
        table = Table(
            table_data,
            colWidths=[
                0.3 * inch,
                1.8 * inch,
                2.2 * inch,
                0.3 * inch,
                0.3 * inch,
                0.3 * inch,
                0.5 * inch,
                0.7 * inch,
            ],
        )

        # Apply table styling
        table_style = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )

        # Color code by risk level - only for rows that exist in the table
        for i, fm in enumerate(critical_modes, 1):
            rpn = fm.get("rpn", 0)
            if i <= len(critical_modes):  # Ensure we don't exceed table rows
                if rpn >= 300:
                    table_style.add("BACKGROUND", (7, i), (7, i), colors.red)
                    table_style.add("TEXTCOLOR", (7, i), (7, i), colors.white)
                elif rpn >= 125:
                    table_style.add("BACKGROUND", (7, i), (7, i), colors.orange)

        table.setStyle(table_style)
        elements.append(table)

        # Add a detailed table for causes and effects
        if len(failure_modes) > 0:
            elements.append(Spacer(1, 0.3 * inch))
            elements.append(
                Paragraph("Detailed Failure Analysis", self.styles["CustomHeading2"])
            )
            elements.append(Spacer(1, 0.1 * inch))

            # Create detailed table with causes and recommendations
            detail_headers = [
                "Component",
                "Failure Mode",
                "Root Cause",
                "Effect",
                "Recommendation",
            ]
            detail_data = [detail_headers]

            for fm in critical_modes[:10]:  # Top 10 for detailed analysis
                comp_para = Paragraph(fm.get("component", ""), self.styles["BodyText"])
                mode_para = Paragraph(
                    fm.get("failure_mode", ""), self.styles["BodyText"]
                )
                cause_para = Paragraph(
                    fm.get("cause", "Not specified"), self.styles["BodyText"]
                )
                effect_para = Paragraph(
                    fm.get("effect", "Not specified"), self.styles["BodyText"]
                )
                rec_para = Paragraph(
                    fm.get("recommendation", "Review design"), self.styles["BodyText"]
                )

                detail_row = [comp_para, mode_para, cause_para, effect_para, rec_para]
                detail_data.append(detail_row)

            detail_table = Table(
                detail_data,
                colWidths=[1.8 * inch, 1.8 * inch, 2.0 * inch, 2.0 * inch, 2.4 * inch],
            )
            detail_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.lightgrey],
                        ),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            elements.append(detail_table)

        return elements

    def _create_risk_matrix(self, failure_modes: List[Dict]) -> List:
        """Create risk assessment matrix"""
        elements = []

        elements.append(
            Paragraph("Risk Assessment Matrix", self.styles["CustomHeading1"])
        )
        elements.append(Spacer(1, 0.1 * inch))

        # Group failure modes by risk level
        critical = [fm for fm in failure_modes if fm.get("rpn", 0) >= 300]
        high = [fm for fm in failure_modes if 125 <= fm.get("rpn", 0) < 300]
        medium = [fm for fm in failure_modes if 50 <= fm.get("rpn", 0) < 125]
        low = [fm for fm in failure_modes if fm.get("rpn", 0) < 50]

        # Create risk summary
        risk_data = [
            ["Risk Level", "RPN Range", "Count", "Action Required"],
            ["Critical", "≥ 300", str(len(critical)), "Immediate action required"],
            ["High", "125-299", str(len(high)), "Action required before production"],
            ["Medium", "50-124", str(len(medium)), "Monitor and improve if feasible"],
            ["Low", "< 50", str(len(low)), "Acceptable risk level"],
        ]

        risk_table = Table(
            risk_data, colWidths=[1.5 * inch, 1.5 * inch, 1 * inch, 2.5 * inch]
        )
        risk_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BACKGROUND", (0, 1), (-1, 1), colors.red),
                    ("BACKGROUND", (0, 2), (-1, 2), colors.orange),
                    ("BACKGROUND", (0, 3), (-1, 3), colors.yellow),
                    ("BACKGROUND", (0, 4), (-1, 4), colors.lightgreen),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(risk_table)

        return elements

    def _create_recommendations(self, failure_modes: List[Dict]) -> List:
        """Create recommendations section"""
        elements = []

        elements.append(Paragraph("Recommendations", self.styles["CustomHeading1"]))
        elements.append(Spacer(1, 0.1 * inch))

        # Get high priority items
        high_priority = sorted(
            [fm for fm in failure_modes if fm.get("rpn", 0) >= 125],
            key=lambda x: x.get("rpn", 0),
            reverse=True,
        )[
            :5
        ]  # Top 5

        if high_priority:
            elements.append(
                Paragraph("Priority Actions", self.styles["CustomHeading2"])
            )

            for fm in high_priority:
                recommendation = fm.get(
                    "recommendation", "Review and implement appropriate mitigation"
                )
                bullet = f"• <b>{fm.get('component', '')}</b> - {fm.get('failure_mode', '')}: {recommendation}"
                elements.append(Paragraph(bullet, self.styles["CustomBody"]))

        # General recommendations
        elements.append(
            Paragraph("General Recommendations", self.styles["CustomHeading2"])
        )

        general_recs = [
            "Implement design review process with focus on high-RPN items",
            "Establish component derating guidelines (50-80% of maximum ratings)",
            "Add test points for critical signals to improve detection capability",
            "Implement thermal analysis and management for power components",
            "Establish incoming inspection procedures for critical components",
            "Document lessons learned and update FMEA regularly",
        ]

        for rec in general_recs:
            elements.append(Paragraph(f"• {rec}", self.styles["CustomBody"]))

        return elements

    def _get_risk_level(self, rpn: int) -> str:
        """Determine risk level based on RPN"""
        if rpn >= 300:
            return "Critical"
        elif rpn >= 125:
            return "High"
        elif rpn >= 50:
            return "Medium"
        else:
            return "Low"

    def _get_status_indicator(self, is_good: bool) -> str:
        """Get status indicator for findings"""
        return "✓ Good" if is_good else "⚠ Attention"


def analyze_circuit_for_fmea(circuit_path: str) -> Tuple[Dict, List[Dict]]:
    """
    Analyze a circuit design and generate FMEA data

    Args:
        circuit_path: Path to circuit files (Python, JSON, or KiCad)

    Returns:
        Tuple of (circuit_data, failure_modes)
    """
    # This would interface with the actual circuit analysis
    # For now, return example data structure

    circuit_data = {
        "name": "ESP32-C6 Development Board",
        "description": "Development board featuring ESP32-C6 microcontroller with USB-C interface",
        "component_count": 15,
        "subsystem_count": 5,
        "subsystems": [
            {
                "name": "USB-C Interface",
                "description": "USB-C connector with ESD protection",
            },
            {"name": "Power Supply", "description": "5V to 3.3V linear regulation"},
            {
                "name": "ESP32-C6 MCU",
                "description": "Main microcontroller with WiFi/BLE",
            },
            {
                "name": "Debug Interface",
                "description": "Programming and debugging header",
            },
            {"name": "Status LED", "description": "User indication LED"},
        ],
    }

    # Example failure modes (would be generated by analysis)
    failure_modes = [
        {
            "component": "USB-C Connector",
            "failure_mode": "Solder joint failure",
            "effect": "Loss of power/data",
            "severity": 9,
            "occurrence": 6,
            "detection": 7,
            "rpn": 378,
            "recommendation": "Add mechanical support and thicker copper pours",
        },
        {
            "component": "AMS1117",
            "failure_mode": "Thermal shutdown",
            "effect": "System power loss",
            "severity": 8,
            "occurrence": 7,
            "detection": 6,
            "rpn": 336,
            "recommendation": "Improve thermal management with vias and copper pour",
        },
        # Add more failure modes as needed
    ]

    return circuit_data, failure_modes


def main():
    """Main function to demonstrate FMEA report generation"""

    # Check if reportlab is available
    if not REPORTLAB_AVAILABLE:
        print("Error: reportlab is required for PDF generation")
        print("Install with: uv pip install reportlab")
        return

    # Create report generator
    generator = FMEAReportGenerator(
        project_name="ESP32-C6 Development Board", author="Circuit-Synth FMEA Analyzer"
    )

    # Analyze circuit (would use actual circuit files)
    circuit_data, failure_modes = analyze_circuit_for_fmea("ESP32_C6_Dev_Board")

    # Generate PDF report
    output_file = generator.generate_fmea_report(
        circuit_data=circuit_data,
        failure_modes=failure_modes,
        output_path="ESP32_C6_FMEA_Report.pdf",
    )

    if output_file:
        print(f"✅ FMEA PDF Report generated successfully: {output_file}")
        print(f"📄 Open the report to review the analysis")
    else:
        print("❌ Failed to generate FMEA report")


if __name__ == "__main__":
    main()
