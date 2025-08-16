"""
Fast Circuit Generation Module

High-speed circuit generation using Google ADK and OpenRouter Gemini-2.5-Flash
for common circuit patterns with KiCad component validation.
"""

from .core import FastCircuitGenerator
from .patterns import CircuitPatterns, PatternType
from .models import OpenRouterModel, GoogleADKModel

__all__ = [
    "FastCircuitGenerator", 
    "CircuitPatterns",
    "PatternType",
    "OpenRouterModel",
    "GoogleADKModel"
]