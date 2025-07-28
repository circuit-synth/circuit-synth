"""
KiCad API - Comprehensive KiCad Manipulation Library

A production-ready library for programmatic manipulation of KiCad schematics,
combining Circuit Synth's robustness with user-friendly patterns inspired by kicad-skip.

Key Features:
- Component management (add, remove, move, clone)
- Wire creation and routing
- Label and annotation management
- Spatial search and discovery
- Connection tracing
- Hierarchical design support

This library is designed to be standalone and suitable for open-source release.
"""

__version__ = "0.5.0"
__author__ = "Circuit Synth Team"

# Import core functionality
from .core import (  # Enums; Core data structures; Search types; Connection types; Parser; Symbol cache
    BoundingBox,
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
    SExpressionParser,
    Sheet,
    SheetPin,
    SymbolDefinition,
    SymbolLibraryCache,
    Text,
    Wire,
    WireRoutingStyle,
    WireStyle,
    get_symbol_cache,
)

# Try to import schematic operations - handle missing imports gracefully
try:
    from .schematic import (  # Wire Management (newly added); Synchronization (existing)
        APISynchronizer,
        ConnectionMatchStrategy,
        ConnectionPoint,
        ConnectionUpdate,
        ConnectionUpdater,
        NetMatcher,
        ReferenceMatchStrategy,
        RoutingConstraints,
        SyncAdapter,
        SyncReport,
        SyncStrategy,
        ValueFootprintStrategy,
        WireManager,
        WireRouter,
    )

    _schematic_imports_available = True
except ImportError as e:
    # If imports fail, set flag but don't crash
    _schematic_imports_available = False
    import warnings

    warnings.warn(f"Some schematic imports not available: {e}")

# Build __all__ based on what's available
__all__ = [
    # Version info
    "__version__",
    "__author__",
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

# Add schematic exports if available
if _schematic_imports_available:
    __all__.extend(
        [
            # Wire management
            "WireManager",
            "ConnectionPoint",
            "WireRouter",
            "RoutingConstraints",
            "ConnectionUpdater",
            "ConnectionUpdate",
            # Synchronization
            "APISynchronizer",
            "SyncReport",
            "SyncAdapter",
            "NetMatcher",
            "SyncStrategy",
            "ReferenceMatchStrategy",
            "ValueFootprintStrategy",
            "ConnectionMatchStrategy",
        ]
    )
