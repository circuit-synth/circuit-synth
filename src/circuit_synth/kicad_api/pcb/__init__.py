"""
KiCad PCB API for creating and manipulating PCB files.

This module provides a simple API for working with KiCad PCB files,
focusing on basic operations like adding, moving, and removing footprints.
"""

from .footprint_library import FootprintInfo, FootprintLibraryCache, get_footprint_cache
from .kicad_cli import DRCResult, KiCadCLI, KiCadCLIError, get_kicad_cli
from .pcb_board import PCBBoard
from .pcb_parser import PCBParser
from .types import Footprint, Layer, Pad

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
