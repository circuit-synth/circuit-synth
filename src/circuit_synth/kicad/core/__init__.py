"""
Core module for KiCad API.

This module contains fundamental components:
- Data types and structures
- S-expression parser
- Symbol library cache
"""

from .s_expression import SExpressionParser
from .symbol_cache import SymbolDefinition, SymbolLibraryCache, get_symbol_cache
from .types import (
    BoundingBox,  # Enums; Core data structures; Search types; Connection types
)
from .types import (
    ConnectionEdge,
    ConnectionNode,
    ElementType,
    Junction,
    Label,
    LabelType,
    Net,
    NetTrace,
    PlacementStrategy,
    Point,
    Schematic,
    SchematicPin,
    SchematicSymbol,
    SearchCriteria,
    SearchResult,
    Sheet,
    SheetPin,
    SymbolInstance,
    Text,
    Wire,
    WireRoutingStyle,
    WireStyle,
)

__all__ = [
    # Enums
    "ElementType",
    "WireRoutingStyle",
    "WireStyle",
    "LabelType",
    "PlacementStrategy",
    # Core data structures
    "Point",
    "BoundingBox",
    "SchematicPin",
    "SymbolInstance",
    "SchematicSymbol",
    "Wire",
    "Label",
    "Text",
    "Junction",
    "Sheet",
    "SheetPin",
    "Net",
    "Schematic",
    # Search types
    "SearchCriteria",
    "SearchResult",
    # Connection types
    "ConnectionNode",
    "ConnectionEdge",
    "NetTrace",
    # Parser
    "SExpressionParser",
    # Symbol cache
    "SymbolLibraryCache",
    "SymbolDefinition",
    "get_symbol_cache",
]
