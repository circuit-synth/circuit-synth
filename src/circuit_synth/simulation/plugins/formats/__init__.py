"""
Format Plugins for Circuit-Synth Simulation Reports

This module contains plugins for different simulation report formats.
All plugins implement the FormatPlugin interface.

Available Format Plugins:
- HTMLFormatPlugin: Interactive HTML reports with Plotly charts
- JSONFormatPlugin: Machine-readable JSON data export

Custom format plugins can be added by:
1. Inheriting from FormatPlugin
2. Implementing all abstract methods  
3. Placing the plugin file in this directory
"""

from .html_format import HTMLFormatPlugin
from .json_format import JSONFormatPlugin

__all__ = [
    'HTMLFormatPlugin',
    'JSONFormatPlugin'
]