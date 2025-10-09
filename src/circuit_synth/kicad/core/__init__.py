"""
Core module for KiCad API.

This module re-exports core types from kicad-sch-api and adds circuit-synth
specific extensions for backward compatibility.
"""

# Import core types from kicad-sch-api (the authoritative source)
# Use parser directly
from kicad_sch_api.core.parser import SExpressionParser

# Import all types from kicad-sch-api types module
from kicad_sch_api.core.types import (
    Junction,
    Label,
    LabelType,
    Net,
    Point,
    Rectangle,
    Schematic,
    SchematicPin,
    SchematicSymbol,
    Sheet,
    SheetPin,
    SymbolInstance,
    Text,
    Wire,
)

# Import circuit-synth specific extensions
from .types_extensions import (
    BoundingBox,
    ConnectionEdge,
    ConnectionNode,
    ElementType,
    NetTrace,
    PlacementStrategy,
    SearchCriteria,
    SearchResult,
    WireRoutingStyle,
    WireStyle,
)

# Import symbol cache (circuit-synth specific)
from .symbol_cache import SymbolDefinition, SymbolLibraryCache, get_symbol_cache

__all__ = [
    # Enums
    "ElementType",
    "WireRoutingStyle",
    "WireStyle",
    "LabelType",
    "PlacementStrategy",
    # Core data structures from kicad-sch-api
    "Point",
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
    "Rectangle",
    # Circuit-synth extensions
    "BoundingBox",
    "SearchCriteria",
    "SearchResult",
    "ConnectionNode",
    "ConnectionEdge",
    "NetTrace",
    # Parser from kicad-sch-api
    "SExpressionParser",
    # Symbol cache (circuit-synth specific)
    "SymbolLibraryCache",
    "SymbolDefinition",
    "get_symbol_cache",
]
