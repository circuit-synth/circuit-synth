"""
Schematic operations module for KiCad API.
Provides high-level operations for manipulating KiCad schematics.
"""

# Component management (if exists)
try:
    from .component_manager import ComponentManager
    from .placement import PlacementEngine, PlacementStrategy
except ImportError:
    pass

from .connection_updater import ConnectionUpdate, ConnectionUpdater

# Wire management - newly added
from .wire_manager import ConnectionPoint, WireManager
from .wire_router import RoutingConstraints, WireRouter

# Other modules (if they exist)
try:
    from .connection_tracer import (
        ConnectionEdge,
        ConnectionGraph,
        ConnectionNode,
        ConnectionTracer,
        NetTrace,
    )
    from .connection_utils import (
        distance_between_points,
        find_pin_by_name,
        get_pin_position,
        points_equal,
        snap_to_grid,
    )
    from .hierarchy_navigator import HierarchyNavigator, HierarchyNode
    from .junction_manager import JunctionManager
    from .label_manager import LabelManager
    from .label_utils import (
        LabelPosition,
        calculate_text_bounds,
        find_connected_labels,
        format_net_name,
        get_wire_direction_at_point,
        group_labels_by_net,
        suggest_label_for_component_pin,
        suggest_label_position,
        validate_hierarchical_label_name,
    )
    from .net_discovery import (
        HierarchicalNetDiscovery,
        NetDiscovery,
        NetInfo,
        NetStatistics,
    )
    from .search_engine import (
        ComponentValueParser,
        MatchType,
        SearchCriterion,
        SearchEngine,
        SearchQueryBuilder,
        SearchResults,
    )
    from .sheet_manager import SheetManager
    from .sheet_utils import (
        PinSide,
        calculate_pin_spacing,
        calculate_sheet_size_from_content,
        create_sheet_instance_name,
        group_pins_by_function,
        match_hierarchical_labels_to_pins,
        resolve_sheet_filepath,
        suggest_pin_side,
        suggest_sheet_position,
        validate_sheet_filename,
    )
    from .text_manager import TextManager
except ImportError:
    pass

from .net_matcher import NetMatcher
from .sync_adapter import SyncAdapter
from .sync_strategies import (
    ConnectionMatchStrategy,
    ReferenceMatchStrategy,
    SyncStrategy,
    ValueFootprintStrategy,
)

# Synchronization components
from .synchronizer import APISynchronizer, SyncReport

# Build __all__ dynamically based on what's available
__all__ = [
    # Wire management - newly added
    "WireManager",
    "ConnectionPoint",
    "WireRouter",
    "RoutingConstraints",
    "ConnectionUpdater",
    "ConnectionUpdate",
    # Synchronization (always available)
    "APISynchronizer",
    "SyncReport",
    "SyncAdapter",
    "NetMatcher",
    "SyncStrategy",
    "ReferenceMatchStrategy",
    "ValueFootprintStrategy",
    "ConnectionMatchStrategy",
]

# Add other exports if modules exist
_optional_exports = [
    # Component management
    "ComponentManager",
    "PlacementEngine",
    "PlacementStrategy",
    # Wire management
    "JunctionManager",
    # Label and text management
    "LabelManager",
    "TextManager",
    "LabelPosition",
    "suggest_label_position",
    "get_wire_direction_at_point",
    "format_net_name",
    "validate_hierarchical_label_name",
    "group_labels_by_net",
    "find_connected_labels",
    "suggest_label_for_component_pin",
    "calculate_text_bounds",
    # Sheet and hierarchy management
    "SheetManager",
    "HierarchyNavigator",
    "HierarchyNode",
    "PinSide",
    "calculate_sheet_size_from_content",
    "suggest_pin_side",
    "match_hierarchical_labels_to_pins",
    "validate_sheet_filename",
    "resolve_sheet_filepath",
    "calculate_pin_spacing",
    "group_pins_by_function",
    "suggest_sheet_position",
    "create_sheet_instance_name",
    # Utilities
    "snap_to_grid",
    "points_equal",
    "distance_between_points",
    "get_pin_position",
    "find_pin_by_name",
    # Search and discovery
    "SearchEngine",
    "SearchQueryBuilder",
    "SearchCriterion",
    "SearchResults",
    "MatchType",
    "ComponentValueParser",
    "ConnectionTracer",
    "ConnectionGraph",
    "ConnectionNode",
    "ConnectionEdge",
    "NetTrace",
    "NetDiscovery",
    "HierarchicalNetDiscovery",
    "NetInfo",
    "NetStatistics",
]

# Add optional exports if they're available
for export in _optional_exports:
    if export in globals():
        __all__.append(export)
