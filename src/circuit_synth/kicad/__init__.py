"""KiCad integration package."""

from .kicad_symbol_cache import SymbolLibCache
from .project_notes import ProjectNotesManager

__all__ = ["ProjectNotesManager", "SymbolLibCache"]
