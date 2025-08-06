"""
Core data types for KiCad API.

This module defines the fundamental data structures used throughout the API.
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union


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


class LabelType(Enum):
    """Types of labels in schematics."""

    LOCAL = "label"
    GLOBAL = "global_label"
    HIERARCHICAL = "hierarchical_label"


class PlacementStrategy(Enum):
    """Component placement strategies."""

    EDGE = "edge"
    GRID = "grid"
    CONTEXTUAL = "contextual"


@dataclass
class Point:
    """2D point in schematic space."""

    x: float
    y: float

    def __iter__(self):
        """Allow tuple unpacking."""
        yield self.x
        yield self.y

    def __getitem__(self, index):
        """Allow indexing."""
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        else:
            raise IndexError("Point index out of range")

    def to_tuple(self) -> Tuple[float, float]:
        """Convert to tuple."""
        return (self.x, self.y)


@dataclass
class BoundingBox:
    """Rectangular bounding box."""

    x1: float
    y1: float
    x2: float
    y2: float

    def __post_init__(self):
        """Ensure x1,y1 is bottom-left and x2,y2 is top-right."""
        self.x1, self.x2 = min(self.x1, self.x2), max(self.x1, self.x2)
        self.y1, self.y2 = min(self.y1, self.y2), max(self.y1, self.y2)

    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is within bounding box."""
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def intersects(self, other: "BoundingBox") -> bool:
        """Check if two bounding boxes intersect."""
        return not (
            self.x2 < other.x1
            or self.x1 > other.x2
            or self.y2 < other.y1
            or self.y1 > other.y2
        )

    @property
    def width(self) -> float:
        """Get width of bounding box."""
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        """Get height of bounding box."""
        return self.y2 - self.y1

    @property
    def center(self) -> Point:
        """Get center point of bounding box."""
        return Point((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)


@dataclass
class SchematicPin:
    """Pin definition for a component."""

    number: str
    name: str
    type: str  # input, output, bidirectional, power, etc.
    position: Point
    orientation: int = 0  # 0, 90, 180, 270 degrees
    length: float = 2.54  # Pin length in mm

    @property
    def uuid(self) -> str:
        """Generate UUID for pin."""
        return str(uuid.uuid4())


@dataclass
class SymbolInstance:
    """Instance information for a symbol in a specific project/path."""

    project: str
    path: str
    reference: str
    unit: int = 1


@dataclass
class SchematicSymbol:
    """Component representation in schematic."""

    reference: str
    value: str
    lib_id: str
    position: Point
    rotation: float = 0.0
    footprint: Optional[str] = None
    properties: Dict[str, str] = field(default_factory=dict)
    pins: List[SchematicPin] = field(default_factory=list)
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    unit: int = 1
    in_bom: bool = True
    on_board: bool = True
    dnp: bool = False
    mirror: Optional[str] = None  # "x" or "y"
    instances: List[SymbolInstance] = field(default_factory=list)

    def get_bounding_box(self) -> BoundingBox:
        """Calculate bounding box for component."""
        # Simplified - would need symbol data for accurate calculation
        size = 25.4  # Default 1 inch size
        return BoundingBox(
            self.position.x - size / 2,
            self.position.y - size / 2,
            self.position.x + size / 2,
            self.position.y + size / 2,
        )


@dataclass
class Wire:
    """Wire connection in schematic."""

    points: List[Point]
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    stroke_width: float = 0.0
    stroke_type: str = "default"

    def get_endpoints(self) -> Tuple[Point, Point]:
        """Get start and end points."""
        return self.points[0], self.points[-1]

    def contains_point(self, point: Point, tolerance: float = 0.01) -> bool:
        """Check if point lies on wire."""
        # Check each segment
        for i in range(len(self.points) - 1):
            if self._point_on_segment(
                point, self.points[i], self.points[i + 1], tolerance
            ):
                return True
        return False

    def _point_on_segment(self, p: Point, a: Point, b: Point, tolerance: float) -> bool:
        """Check if point p is on line segment a-b."""
        # Calculate distance from point to line
        # This is a simplified version - full implementation would be more robust
        cross = (p.y - a.y) * (b.x - a.x) - (p.x - a.x) * (b.y - a.y)
        if abs(cross) > tolerance:
            return False

        # Check if point is within segment bounds
        dot = (p.x - a.x) * (b.x - a.x) + (p.y - a.y) * (b.y - a.y)
        squared_length = (b.x - a.x) ** 2 + (b.y - a.y) ** 2

        if squared_length == 0:
            return (p.x - a.x) ** 2 + (p.y - a.y) ** 2 <= tolerance**2

        param = dot / squared_length
        return 0 <= param <= 1


@dataclass
class Label:
    """Label in schematic."""

    text: str
    position: Point
    label_type: LabelType = LabelType.LOCAL
    orientation: int = 0  # 0, 90, 180, 270
    effects: Optional[Dict[str, Any]] = None
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Junction:
    """Junction point where wires meet."""

    position: Point
    diameter: float = 0.9144  # Default diameter in mm
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Text:
    """Text annotation in schematic."""

    content: str
    position: Point
    orientation: int = 0  # 0, 90, 180, 270
    size: float = 1.27  # Default text size in mm
    effects: Optional[Dict[str, Any]] = None
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Sheet:
    """Hierarchical sheet in schematic."""

    name: str
    filename: str
    position: Point
    size: Tuple[float, float]  # width, height
    pins: List["SheetPin"] = field(default_factory=list)
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class SheetPin:
    """Pin on a hierarchical sheet."""

    name: str
    position: Point
    orientation: int  # 0, 90, 180, 270
    shape: str = "input"  # input, output, bidirectional, tri_state, passive
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Rectangle:
    """Rectangle graphic element in schematic."""

    start: Point
    end: Point
    stroke_width: float = 0.127
    stroke_type: str = "solid"
    fill_type: str = "none"
    stroke_color: Optional[str] = None  # For medium gray
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Net:
    """Electrical net connecting components."""

    name: str
    nodes: List[Tuple[str, str]] = field(default_factory=list)  # (reference, pin)

    def add_node(self, reference: str, pin: str):
        """Add a node to the net."""
        self.nodes.append((reference, pin))


@dataclass
class Schematic:
    """Complete schematic representation."""

    version: str = "20250114"
    generator: str = "circuit_synth"
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    date: str = ""
    revision: str = ""
    company: str = ""
    comment: str = ""

    components: List[SchematicSymbol] = field(default_factory=list)
    wires: List[Wire] = field(default_factory=list)
    labels: List[Label] = field(default_factory=list)
    texts: List[Text] = field(default_factory=list)
    junctions: List[Junction] = field(default_factory=list)
    sheets: List[Sheet] = field(default_factory=list)
    nets: List[Net] = field(default_factory=list)
    rectangles: List[Rectangle] = field(default_factory=list)

    # Hierarchical path for sheet_instances generation
    hierarchical_path: List[str] = field(default_factory=list)

    def get_component(self, reference: str) -> Optional[SchematicSymbol]:
        """Get component by reference."""
        for comp in self.components:
            if comp.reference == reference:
                return comp
        return None

    def add_component(self, component: SchematicSymbol):
        """Add component to schematic."""
        self.components.append(component)

    def remove_component(self, reference: str) -> bool:
        """Remove component by reference."""
        for i, comp in enumerate(self.components):
            if comp.reference == reference:
                del self.components[i]
                return True
        return False

    def add_wire(self, wire: Wire):
        """Add wire to schematic."""
        self.wires.append(wire)

    def add_label(self, label: Label):
        """Add label to schematic."""
        self.labels.append(label)

    def add_text(self, text: Text):
        """Add text to schematic."""
        self.texts.append(text)

    def add_junction(self, junction: Junction):
        """Add junction to schematic."""
        self.junctions.append(junction)

    def add_rectangle(self, rectangle: Rectangle):
        """Add rectangle graphic to schematic."""
        self.rectangles.append(rectangle)


# Search-related types
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
