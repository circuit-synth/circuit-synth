"""
Abstract interfaces for extensibility
"""

from .circuit_interface import ICircuitModel
from .kicad_interface import IKiCadIntegration, KiCadGenerationConfig

__all__ = [
    "IKiCadIntegration",
    "KiCadGenerationConfig",
    "ICircuitModel",
]
