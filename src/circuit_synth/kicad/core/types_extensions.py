"""
Circuit-synth specific type extensions for KiCad API.

This module contains additional types and enums specific to circuit-synth
that extend the core kicad-sch-api types.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# Import core types from kicad-sch-api
from kicad_sch_api.core.types import Junction, Label, Point, SchematicSymbol, Wire


class ElementType(Enum):
    """Types of schematic elements."""

    COMPONENT = "symbol"
    WIRE = "wire"
    LABEL = "label"
    GLOBAL_LABEL = "global_label"
    HIERARCHICAL_LABEL = "hierarchical_label"
    JUNCTION = "junction"
    NO_CONNECT = "no_connect"
    TEXT = "text"
    SHEET = "sheet"
    SHEET_PIN = "sheet_pin"


class WireRoutingStyle(Enum):
    """Wire routing algorithms."""

    DIRECT = "direct"
    MANHATTAN = "manhattan"
    DIAGONAL = "diagonal"


class WireStyle(Enum):
    """Wire update styles for component moves."""

    MAINTAIN = "maintain"
    REDRAW = "redraw"
    STRETCH = "stretch"


class PlacementStrategy(Enum):
    """Component placement strategies."""

    SEQUENTIAL = "sequential"
    CONNECTION_AWARE = "connection_aware"
    HIERARCHICAL = "hierarchical"
    LLM = "llm"


@dataclass
class BoundingBox:
    """Axis-aligned bounding box."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @property
    def width(self) -> float:
        """Get box width."""
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        """Get box height."""
        return self.max_y - self.min_y

    @property
    def center(self) -> Point:
        """Get box center point."""
        return Point((self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2)

    def contains(self, point: Point) -> bool:
        """Check if point is inside box."""
        return (
            self.min_x <= point.x <= self.max_x and self.min_y <= point.y <= self.max_y
        )

    def overlaps(self, other: "BoundingBox") -> bool:
        """Check if this box overlaps with another."""
        return not (
            self.max_x < other.min_x
            or self.min_x > other.max_x
            or self.max_y < other.min_y
            or self.min_y > other.max_y
        )

    def expand(self, margin: float) -> "BoundingBox":
        """Return expanded bounding box with added margin."""
        return BoundingBox(
            self.min_x - margin,
            self.min_y - margin,
            self.max_x + margin,
            self.max_y + margin,
        )


@dataclass
class SearchCriteria:
    """Criteria for component search."""

    reference_pattern: Optional[str] = None
    value_pattern: Optional[str] = None
    lib_id_pattern: Optional[str] = None
    property_filters: Dict[str, str] = field(default_factory=dict)
    area: Optional[BoundingBox] = None
    use_regex: bool = False


@dataclass
class SearchResult:
    """Result of a search operation."""

    components: List[SchematicSymbol] = field(default_factory=list)
    wires: List[Wire] = field(default_factory=list)
    labels: List[Label] = field(default_factory=list)
    junctions: List[Junction] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        """Get total number of results."""
        return (
            len(self.components)
            + len(self.wires)
            + len(self.labels)
            + len(self.junctions)
        )

    def get_all_elements(self) -> List[Any]:
        """Get all elements regardless of type."""
        return self.components + self.wires + self.labels + self.junctions


# Connection tracing types
@dataclass
class ConnectionNode:
    """Node in connection graph."""

    element: Any  # Component, junction, or label
    element_type: ElementType
    position: Point
    connections: List["ConnectionEdge"] = field(default_factory=list)


@dataclass
class ConnectionEdge:
    """Edge in connection graph."""

    wire: Wire
    start_node: ConnectionNode
    end_node: ConnectionNode


@dataclass
class NetTrace:
    """Result of tracing a net."""

    components: List[SchematicSymbol] = field(default_factory=list)
    wires: List[Wire] = field(default_factory=list)
    labels: List[Label] = field(default_factory=list)
    junctions: List[Junction] = field(default_factory=list)
    net_name: Optional[str] = None
