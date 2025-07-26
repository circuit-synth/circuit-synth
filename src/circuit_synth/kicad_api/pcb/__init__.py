"""
KiCad PCB API for creating and manipulating PCB files.

This module provides a simple API for working with KiCad PCB files,
focusing on basic operations like adding, moving, and removing footprints.
"""

from .pcb_board import PCBBoard
from .pcb_parser import PCBParser
from .types import Footprint, Pad, Layer
from .kicad_cli import KiCadCLI, get_kicad_cli, DRCResult, KiCadCLIError
from .footprint_library import FootprintLibraryCache, FootprintInfo, get_footprint_cache

__all__ = [
    'PCBBoard',
    'PCBParser',
    'Footprint',
    'Pad',
    'Layer',
    'KiCadCLI',
    'get_kicad_cli',
    'DRCResult',
    'KiCadCLIError',
    'FootprintLibraryCache',
    'FootprintInfo',
    'get_footprint_cache'
]