"""
Circuit Debugging Module for AI-Powered PCB Troubleshooting

This module provides intelligent debugging assistance for PCB and circuit issues,
including schematic analysis, test data interpretation, and troubleshooting guidance.
"""

from .analyzer import (
    CircuitDebugger, 
    DebugSession,
    DebugCategory,
    IssueSeverity,
    DebugIssue
)
from .symptoms import (
    SymptomAnalyzer, 
    TestMeasurement,
    MeasurementType,
    OscilloscopeTrace
)
from .knowledge_base import (
    DebugKnowledgeBase, 
    DebugPattern,
    ComponentFailure
)
from .test_guidance import (
    TestGuidance, 
    TroubleshootingTree,
    TestStep,
    TestEquipment
)

__all__ = [
    'CircuitDebugger',
    'DebugSession',
    'DebugCategory',
    'IssueSeverity',
    'DebugIssue',
    'SymptomAnalyzer',
    'TestMeasurement',
    'MeasurementType',
    'OscilloscopeTrace',
    'DebugKnowledgeBase',
    'DebugPattern',
    'ComponentFailure',
    'TestGuidance',
    'TroubleshootingTree',
    'TestStep',
    'TestEquipment',
]