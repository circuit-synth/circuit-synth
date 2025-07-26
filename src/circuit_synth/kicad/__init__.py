"""KiCad integration package."""

from .project_notes import ProjectNotesManager
from .kicad_symbol_cache import SymbolLibCache

__all__ = ['ProjectNotesManager', 'SymbolLibCache']
