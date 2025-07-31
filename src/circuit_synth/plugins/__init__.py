"""
Circuit-Synth KiCad Plugin Integration

This module provides integration between circuit-synth and KiCad plugins,
including the Smarton AI plugin for intelligent circuit design assistance.
"""

from .smarton_ai_bridge import SmartonAIBridge

__all__ = ["SmartonAIBridge"]
