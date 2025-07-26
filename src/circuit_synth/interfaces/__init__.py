"""
Abstract interfaces for extensibility
"""

from .kicad_interface import IKiCadIntegration, KiCadGenerationConfig
from .circuit_interface import ICircuitModel

__all__ = [
    'IKiCadIntegration',
    'KiCadGenerationConfig',
    'ICircuitModel',
]