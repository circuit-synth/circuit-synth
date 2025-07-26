"""
Core module for KiCad API.

This module contains fundamental components:
- Data types and structures
- S-expression parser
- Symbol library cache
"""

from .types import (
    # Enums
    ElementType,
    WireRoutingStyle,
    WireStyle,
    LabelType,
    PlacementStrategy,
    
    # Core data structures
    Point,
    BoundingBox,
    SchematicPin,
    SymbolInstance,
    SchematicSymbol,
    Wire,
    Label,
    Text,
    Junction,
    Sheet,
    SheetPin,
    Net,
    Schematic,
    
    # Search types
    SearchCriteria,
    SearchResult,
    
    # Connection types
    ConnectionNode,
    ConnectionEdge,
    NetTrace,
)

from .s_expression import SExpressionParser
from .symbol_cache import SymbolLibraryCache, SymbolDefinition, get_symbol_cache

__all__ = [
    # Enums
    'ElementType',
    'WireRoutingStyle',
    'WireStyle',
    'LabelType',
    'PlacementStrategy',
    
    # Core data structures
    'Point',
    'BoundingBox',
    'SchematicPin',
    'SymbolInstance',
    'SchematicSymbol',
    'Wire',
    'Label',
    'Text',
    'Junction',
    'Sheet',
    'SheetPin',
    'Net',
    'Schematic',
    
    # Search types
    'SearchCriteria',
    'SearchResult',
    
    # Connection types
    'ConnectionNode',
    'ConnectionEdge',
    'NetTrace',
    
    # Parser
    'SExpressionParser',
    
    # Symbol cache
    'SymbolLibraryCache',
    'SymbolDefinition',
    'get_symbol_cache',
]