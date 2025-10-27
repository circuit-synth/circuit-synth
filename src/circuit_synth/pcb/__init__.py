"""
KiCad PCB API for creating and manipulating PCB files.

This module now re-exports from kicad-pcb-api for compatibility.
NEW CODE SHOULD IMPORT DIRECTLY FROM kicad-pcb-api.

Migration to kicad-pcb-api in progress (#325).
This compatibility layer will be removed in v0.12.0.
"""

# Re-export from kicad-pcb-api for backward compatibility
from kicad_pcb_api import PCBBoard, PCBParser
from kicad_pcb_api.core.types import Footprint, Layer, Pad
from kicad_pcb_api.footprints.footprint_library import (
    FootprintInfo,
    FootprintLibraryCache,
    get_footprint_cache,
)

# Keep circuit-synth specific extensions
from .kicad_cli import DRCResult, KiCadCLI, KiCadCLIError, get_kicad_cli

__all__ = [
    "PCBBoard",
    "PCBParser",
    "Footprint",
    "Pad",
    "Layer",
    "KiCadCLI",
    "get_kicad_cli",
    "DRCResult",
    "KiCadCLIError",
    "FootprintLibraryCache",
    "FootprintInfo",
    "get_footprint_cache",
]
