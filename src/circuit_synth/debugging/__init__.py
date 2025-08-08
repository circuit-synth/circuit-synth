"""
Circuit Debugging Module for AI-Powered PCB Troubleshooting

This module provides intelligent debugging assistance for PCB and circuit issues,
including schematic analysis, test data interpretation, and troubleshooting guidance.
"""

from .analyzer import (
    CircuitDebugger,
    DebugCategory,
    DebugIssue,
    DebugSession,
    IssueSeverity,
)
from .knowledge_base import ComponentFailure, DebugKnowledgeBase, DebugPattern
from .symptoms import (
    MeasurementType,
    OscilloscopeTrace,
    SymptomAnalyzer,
    TestMeasurement,
)
from .test_guidance import TestEquipment, TestGuidance, TestStep, TroubleshootingTree

__all__ = [
    "CircuitDebugger",
    "DebugSession",
    "DebugCategory",
    "IssueSeverity",
    "DebugIssue",
    "SymptomAnalyzer",
    "TestMeasurement",
    "MeasurementType",
    "OscilloscopeTrace",
    "DebugKnowledgeBase",
    "DebugPattern",
    "ComponentFailure",
    "TestGuidance",
    "TroubleshootingTree",
    "TestStep",
    "TestEquipment",
]
