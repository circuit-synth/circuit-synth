"""
Circuit-Synth Quality Assurance Module
Provides FMEA, DFM, and other quality analysis tools for circuit designs
"""

from .fmea_analyzer import (
    ComponentType,
    FailureMode,
    UniversalFMEAAnalyzer,
    analyze_any_circuit,
)
from .fmea_report_generator import (
    REPORTLAB_AVAILABLE,
    FMEAReportGenerator,
    analyze_circuit_for_fmea,
)

# Import enhanced analyzer if available
try:
    from .enhanced_fmea_analyzer import EnhancedFMEAAnalyzer

    _has_enhanced = True
except ImportError:
    _has_enhanced = False

# Import comprehensive report generator if available
try:
    from .comprehensive_fmea_report_generator import ComprehensiveFMEAReportGenerator

    _has_comprehensive = True
except ImportError:
    _has_comprehensive = False

__all__ = [
    "FMEAReportGenerator",
    "analyze_circuit_for_fmea",
    "REPORTLAB_AVAILABLE",
    "UniversalFMEAAnalyzer",
    "analyze_any_circuit",
    "ComponentType",
    "FailureMode",
]

# Add conditional exports
if _has_enhanced:
    __all__.append("EnhancedFMEAAnalyzer")
if _has_comprehensive:
    __all__.append("ComprehensiveFMEAReportGenerator")
