#!/usr/bin/env python3
"""
Design for Manufacturing (DFM) Analysis System

Comprehensive DFM analysis for circuit optimization, cost modeling, and manufacturability assessment.
"""

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

# Import comprehensive report generator if reportlab is available
try:
    from .comprehensive_dfm_report_generator import (
        ComprehensiveDFMReportGenerator,
        generate_dfm_report,
    )

    DFM_REPORT_AVAILABLE = True
except ImportError:
    DFM_REPORT_AVAILABLE = False
    ComprehensiveDFMReportGenerator = None
    generate_dfm_report = None

__all__ = [
    # Core DFM analyzer classes
    "DFMAnalyzer",
    "DFMReport",
    "ManufacturingIssue",
    "ComponentAnalysis",
    "PCBAnalysis",
    "ManufacturingProcess",
    "IssueSeverity",
    "IssueCategory",
    # Report generation (conditional)
    "ComprehensiveDFMReportGenerator",
    "generate_dfm_report",
    "DFM_REPORT_AVAILABLE",
]
