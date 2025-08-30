"""
Circuit-Synth Simulation Plugins

This package contains extensible plugins for simulation analysis and report generation.
Plugins are automatically discovered and loaded by the PluginRegistry.

Plugin Types:
- Analysis Plugins: DC, AC, Transient, and custom analysis types
- Format Plugins: HTML, PDF, JSON, and custom output formats

Creating Custom Plugins:
1. Inherit from AnalysisPlugin or FormatPlugin
2. Implement required abstract methods
3. Place in appropriate plugin directory or external package
4. Register via entry_points for external distribution
"""

from .analysis import *
from .formats import *

__all__ = []