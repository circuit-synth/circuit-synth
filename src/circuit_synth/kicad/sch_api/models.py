"""
Data models and enums for the KiCad Schematic API.

These models define the structure of options and results for various operations,
providing a clean interface for component management.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class WireStyle(Enum):
    """Defines how wires should be handled when moving components."""

    MAINTAIN = "maintain"  # Move wire endpoints with component
    REDRAW = "redraw"  # Remove and recreate wires
    STRETCH = "stretch"  # Add intermediate points to maintain angles


class RoutingStyle(Enum):
    """Defines wire routing algorithms."""

    DIRECT = "direct"  # Straight line connection
    ORTHOGONAL = "orthogonal"  # Right-angle routing
    DIAGONAL = "diagonal"  # 45-degree routing


class PlacementStrategy(Enum):
    """Defines component placement strategies."""

    EDGE = "edge"  # Place at edge of existing components
    GRID = "grid"  # Place on next available grid position
    CONTEXTUAL = "contextual"  # Place near related components


@dataclass
class RemovalOptions:
    """Options for component removal operations."""

    remove_connected_wires: bool = False
    remove_orphaned_nets: bool = False
    remove_associated_labels: bool = False
    update_junctions: bool = True
    preserve_user_wires: bool = True


@dataclass
class RemovalResult:
    """Result of a component removal operation."""

    success: bool
    removed_elements: List[Any] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class MoveOptions:
    """Options for component move operations."""

    snap_to_grid: bool = True
    check_collisions: bool = True
    maintain_wires: bool = True
    wire_style: WireStyle = WireStyle.MAINTAIN
    routing_style: RoutingStyle = RoutingStyle.ORTHOGONAL
    update_properties: bool = True


@dataclass
class MoveResult:
    """Result of a component move operation."""

    success: bool
    new_position: Optional[Tuple[float, float]] = None
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None
    wires_updated: int = 0


@dataclass
class CloneOptions:
    """Options for component cloning operations."""

    auto_increment_reference: bool = True
    clone_properties: bool = True
    clone_connections: bool = False
    position_offset: Optional[Tuple[float, float]] = None
    snap_to_grid: bool = True


@dataclass
class PlacementInfo:
    """Information about component placement."""

    position: Tuple[float, float]
    rotation: float = 0.0
    mirror: bool = False
    strategy_used: PlacementStrategy = PlacementStrategy.EDGE


@dataclass
class ComponentUpdate:
    """Represents an update to a component."""

    action: str  # 'add', 'modify', 'remove', 'preserve'
    component: Any  # SchematicSymbol
    placement_info: Optional[PlacementInfo] = None
    old_component: Optional[Any] = None  # For modify operations


@dataclass
class ComponentConnections:
    """Information about a component's connections."""

    wires: List[Any] = field(default_factory=list)  # List[Wire]
    nets: List[Any] = field(default_factory=list)  # List[Net]
    labels: List[Any] = field(default_factory=list)  # List[Label]
    junction_points: List[Tuple[float, float]] = field(default_factory=list)
    connected_components: List[Any] = field(
        default_factory=list
    )  # List[SchematicSymbol]


@dataclass
class PinConnection:
    """Information about a pin connection."""

    pin_number: str
    pin_type: str
    net_name: Optional[str] = None
    position: Optional[Tuple[float, float]] = None
    connected_wires: List[Any] = field(default_factory=list)


@dataclass
class SearchCriteria:
    """Criteria for searching components."""

    reference_pattern: Optional[str] = None
    value_pattern: Optional[str] = None
    footprint_pattern: Optional[str] = None
    lib_id_pattern: Optional[str] = None
    property_filters: Dict[str, str] = field(default_factory=dict)
    use_regex: bool = False
    case_sensitive: bool = True


@dataclass
class AlignmentOptions:
    """Options for component alignment operations."""

    alignment: str = "horizontal"  # 'horizontal', 'vertical', 'grid'
    spacing: Optional[float] = None
    reference_component: Optional[str] = None
    maintain_connections: bool = True


@dataclass
class ValidationResult:
    """Result of component validation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
