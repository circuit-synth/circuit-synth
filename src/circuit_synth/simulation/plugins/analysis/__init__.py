"""
Analysis Plugins for Circuit-Synth Simulation

This module contains plugins for different simulation analysis types.
All plugins implement the AnalysisPlugin interface.

Available Analysis Plugins:
- DCAnalysisPlugin: DC operating point analysis
- ACAnalysisPlugin: AC frequency domain analysis  
- TransientAnalysisPlugin: Time domain transient analysis

Custom analysis plugins can be added by:
1. Inheriting from AnalysisPlugin
2. Implementing all abstract methods
3. Placing the plugin file in this directory
"""

from .dc_analysis import DCAnalysisPlugin
from .ac_analysis import ACAnalysisPlugin  
from .transient_analysis import TransientAnalysisPlugin

__all__ = [
    'DCAnalysisPlugin',
    'ACAnalysisPlugin', 
    'TransientAnalysisPlugin'
]