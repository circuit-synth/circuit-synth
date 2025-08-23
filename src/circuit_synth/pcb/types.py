"""
Data types for KiCad PCB files.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union


class Layer(Enum):
    """PCB layer definitions."""

    F_Cu = "F.Cu"  # Front copper
    B_Cu = "B.Cu"  # Back copper
    F_Adhes = "F.Adhes"  # Front adhesive
    B_Adhes = "B.Adhes"  # Back adhesive
    F_Paste = "F.Paste"  # Front solder paste
    B_Paste = "B.Paste"  # Back solder paste
    F_SilkS = "F.SilkS"  # Front silkscreen
    B_SilkS = "B.SilkS"  # Back silkscreen
    F_Mask = "F.Mask"  # Front solder mask
    B_Mask = "B.Mask"  # Back solder mask
    Dwgs_User = "Dwgs.User"  # User drawings
    Cmts_User = "Cmts.User"  # User comments
    Eco1_User = "Eco1.User"  # User eco1
    Eco2_User = "Eco2.User"  # User eco2
    Edge_Cuts = "Edge.Cuts"  # Board outline
    Margin = "Margin"  # Board margin
    F_CrtYd = "F.CrtYd"  # Front courtyard
    B_CrtYd = "B.CrtYd"  # Back courtyard
    F_Fab = "F.Fab"  # Front fabrication
    B_Fab = "B.Fab"  # Back fabrication


@dataclass
class Point:
    """2D point in PCB coordinates."""

    x: float
    y: float

    def __repr__(self):
        return f"Point({self.x}, {self.y})"


@dataclass
class Pad:
    """PCB pad definition."""

    number: str
    type: str  # "smd", "thru_hole", etc.
    shape: str  # "circle", "rect", "roundrect", etc.
    position: Point  # Relative to footprint origin
    size: Tuple[float, float]  # (width, height)
    rotation: float = 0.0  # Rotation in degrees
    layers: List[str] = field(default_factory=list)
    drill: Optional[Union[float, Dict[str, float]]] = (
        None  # float for circular, dict for oval
    )
    net: Optional[int] = None
    net_name: Optional[str] = None
    roundrect_rratio: Optional[float] = None
    pinfunction: Optional[str] = None  # e.g., "GND", "VBUS", "SHIELD"
    pintype: Optional[str] = None  # e.g., "passive", "bidirectional"
    properties: Dict[str, Any] = field(
        default_factory=dict
    )  # e.g., {"pad_prop_heatsink": True}
    uuid: str = ""


@dataclass
class Line:
    """Graphical line on PCB."""

    start: Point
    end: Point
    layer: str
    width: float = 0.1
    type: str = "solid"
    uuid: str = ""


@dataclass
class Arc:
    """Graphical arc on PCB."""

    start: Point
    mid: Point
    end: Point
    layer: str
    width: float = 0.1
    type: str = "solid"
    uuid: str = ""


@dataclass
class Text:
    """Text on PCB."""

    text: str
    position: Point
    layer: str
    size: Tuple[float, float] = (1.0, 1.0)
    thickness: float = 0.15
    effects: Dict[str, Any] = field(default_factory=dict)
    uuid: str = ""


@dataclass
class Property:
    """Footprint property (Reference, Value, etc.)."""

    name: str
    value: str
    position: Point  # Relative to footprint origin
    layer: str
    size: Tuple[float, float] = (1.0, 1.0)
    thickness: float = 0.15
    effects: Dict[str, Any] = field(default_factory=dict)
    uuid: str = ""


@dataclass
class Footprint:
    """PCB footprint (component physical representation)."""

    library: str  # e.g., "Resistor_SMD"
    name: str  # e.g., "R_0603_1608Metric"
    position: Point  # Absolute position on board
    rotation: float = 0.0  # Rotation in degrees
    layer: str = "F.Cu"  # Primary layer
    reference: str = ""  # e.g., "R1"
    value: str = ""  # e.g., "10k"
    uuid: str = ""
    locked: bool = False
    placed: bool = True

    # Component properties
    properties: List[Property] = field(default_factory=list)

    # Graphical elements
    lines: List[Line] = field(default_factory=list)
    arcs: List[Arc] = field(default_factory=list)
    texts: List[Text] = field(default_factory=list)
    rectangles: List["Rectangle"] = field(default_factory=list)

    # Pads
    pads: List[Pad] = field(default_factory=list)

    # 3D model
    model_path: Optional[str] = None
    model_offset: Optional[Tuple[float, float, float]] = None
    model_scale: Optional[Tuple[float, float, float]] = None
    model_rotate: Optional[Tuple[float, float, float]] = None

    # Additional metadata
    descr: str = ""
    tags: str = ""
    path: str = ""  # Hierarchical path
    sheetname: str = ""
    sheetfile: str = ""
    attr: str = ""  # Attributes like "smd"

    def get_library_id(self) -> str:
        """Get the full library ID (library:name)."""
        return f"{self.library}:{self.name}"

    def get_property(self, name: str) -> Optional[Property]:
        """Get a property by name."""
        for prop in self.properties:
            if prop.name == name:
                return prop
        return None

    def set_property(self, name: str, value: str):
        """Set or update a property value."""
        prop = self.get_property(name)
        if prop:
            prop.value = value
        else:
            # Create new property with default position
            self.properties.append(
                Property(name=name, value=value, position=Point(0, 0), layer=self.layer)
            )


@dataclass
class Net:
    """PCB net definition."""

    number: int
    name: str


@dataclass
class Via:
    """PCB via definition."""

    position: Point
    size: float
    drill: float
    layers: List[str]
    net: Optional[int] = None
    uuid: str = ""


@dataclass
class Track:
    """PCB track (trace) definition."""

    start: Point
    end: Point
    width: float
    layer: str
    net: Optional[int] = None
    net_name: Optional[str] = None
    uuid: str = ""


@dataclass
class Zone:
    """PCB zone (copper pour area)."""

    layer: str
    net: Optional[int] = None
    net_name: Optional[str] = None
    priority: int = 0
    connect_pads: str = "yes"  # "yes", "no", "thermal_reliefs"
    min_thickness: float = 0.25
    filled: bool = True
    fill_mode: str = "solid"  # "solid", "hatch"
    hatch_thickness: float = 0.15
    hatch_gap: float = 0.5
    hatch_orientation: float = 0.0
    thermal_relief_gap: float = 0.5
    thermal_relief_bridge: float = 0.5
    smoothing: str = "none"  # "none", "chamfer", "fillet"
    radius: float = 0.0
    polygon: List[Point] = field(default_factory=list)
    uuid: str = ""


@dataclass
class Rectangle:
    """PCB rectangle graphic definition."""

    start: Point
    end: Point
    layer: str
    width: float = 0.05
    fill: bool = False
    uuid: str = ""
