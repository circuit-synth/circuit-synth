# FILE: src/circuit_synth/kicad/symbol_lib_parser.py
# Unified KiCad symbol parser with graphic elements, pin data, inheritance.

import logging
import os
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

import sexpdata

from circuit_synth.core.exception import (
    LibraryNotFound,
    ParseError,
    SymbolNotFoundError,
)

logger = logging.getLogger(__name__)


@dataclass
class KicadSymbolPin:
    """Represents a pin in a KiCad symbol."""

    pin_id: str
    name: str
    number: str
    function: str  # e.g. "power_in", "passive", "input"
    unit: int
    x: float
    y: float
    length: float
    orientation: float

    def to_simple_dict(self) -> Dict[str, Any]:
        """Convert this pin into a JSON-serializable dict."""
        return {
            "pin_id": self.pin_id,
            "name": self.name,
            "number": self.number,
            "function": self.function,
            "unit": self.unit,
            "x": self.x,
            "y": self.y,
            "length": self.length,
            "orientation": self.orientation,
        }

    @classmethod
    def from_simple_dict(cls, d: Dict[str, Any]) -> "KicadSymbolPin":
        """Recreate a pin object from a dict produced by `to_simple_dict()`."""
        return cls(**d)


@dataclass
class GraphicElement:
    """Represents a graphical shape in a KiCad symbol (rectangle, circle, arc, etc.)."""

    shape_type: str  # "rectangle", "circle", "arc", "polyline", ...
    start: Optional[List[float]]  # e.g. [x, y]
    end: Optional[List[float]]  # e.g. [x, y]
    mid: Optional[List[float]] = None  # Add midpoint for arcs
    points: List[List[float]] = field(default_factory=list)  # For polylines
    radius: Optional[float] = None  # For circles
    stroke_width: float = 0.254
    stroke_type: str = "default"
    fill_type: str = "none"

    def to_simple_dict(self) -> Dict[str, Any]:
        """Convert this graphical element into a JSON-serializable dict."""
        return {
            "shape_type": self.shape_type,
            "start": self.start,
            "end": self.end,
            "mid": self.mid,  # Include midpoint in serialization
            "points": self.points,  # Include points in serialization
            "radius": self.radius,  # Include radius in serialization
            "stroke_width": self.stroke_width,
            "stroke_type": self.stroke_type,
            "fill_type": self.fill_type,
        }

    @classmethod
    def from_simple_dict(cls, d: Dict[str, Any]) -> "GraphicElement":
        """Recreate a graphic object from a dict produced by `to_simple_dict()`."""
        return cls(
            shape_type=d["shape_type"],
            start=d.get("start"),
            end=d.get("end"),
            mid=d.get("mid"),  # Restore midpoint from dict
            points=d.get("points", []),  # Restore points from dict
            radius=d.get("radius"),  # Restore radius from dict
            stroke_width=d.get("stroke_width", 0.254),
            stroke_type=d.get("stroke_type", "default"),
            fill_type=d.get("fill_type", "none"),
        )


@dataclass
class KicadSymbol:
    """
    Represents a KiCad symbol with its properties, pins, graphics, etc.
    Now also stores 'pin_numbers' mode and a 'pin_names_offset' float if found.
    """

    name: str
    reference: str
    properties: Dict[str, str] = field(default_factory=dict)
    pins: List[KicadSymbolPin] = field(default_factory=list)
    graphics: List[GraphicElement] = field(default_factory=list)
    units: Dict[int, List[KicadSymbolPin]] = field(default_factory=dict)
    extends: Optional[str] = None
    is_power: bool = False

    # Additional fields to capture KiCad-style symbol-level settings:
    pin_numbers: Optional[str] = None  # e.g. "hide"
    pin_names_offset: Optional[float] = None  # e.g. 0.254

    def merge_parent(self, parent: "KicadSymbol") -> None:
        """
        Merge parent's attributes into this symbol if extends=parent.
        Child overrides where it has data; otherwise inherits parent's data.
        """
        logger.debug(
            "Merging parent symbol '%s' into child '%s'", parent.name, self.name
        )
        # Merge properties
        for k, v in parent.properties.items():
            if k not in self.properties:
                self.properties[k] = v

        # If child has no pins, inherit parent's pins
        if not self.pins:
            self.pins = deepcopy(parent.pins)

        # Merge or override graphics
        if not self.graphics and parent.graphics:
            self.graphics = deepcopy(parent.graphics)

        # Inherit parent's units if child doesn't define them
        for unit_num, parent_unit_pins in parent.units.items():
            if unit_num not in self.units:
                self.units[unit_num] = deepcopy(parent_unit_pins)

        # Inherit parent's power flag
        if parent.is_power and not self.is_power:
            self.is_power = True

        # Inherit parent's reference if we don't have one
        if not self.reference and parent.reference:
            self.reference = parent.reference

        # Inherit pin_numbers/pin_names_offset
        if parent.pin_numbers and not self.pin_numbers:
            self.pin_numbers = parent.pin_numbers
        if parent.pin_names_offset is not None and self.pin_names_offset is None:
            self.pin_names_offset = parent.pin_names_offset

    def to_simple_dict(self) -> Dict[str, Any]:
        """
        Convert this KicadSymbol into a purely JSON-serializable dictionary.
        """
        return {
            "name": self.name,
            "reference": self.reference,
            "properties": self.properties,
            "pins": [p.to_simple_dict() for p in self.pins],
            "graphics": [g.to_simple_dict() for g in self.graphics],
            "units": {
                str(unit_num): [p.to_simple_dict() for p in pin_list]
                for unit_num, pin_list in self.units.items()
            },
            "extends": self.extends,
            "is_power": self.is_power,
            "pin_numbers": self.pin_numbers,
            "pin_names_offset": self.pin_names_offset,
        }

    @classmethod
    def from_simple_dict(cls, data: Dict[str, Any]) -> "KicadSymbol":
        """
        Rebuild a KicadSymbol from a dictionary that came from `to_simple_dict()`.
        """
        pins = [KicadSymbolPin.from_simple_dict(pd) for pd in data.get("pins", [])]
        graphics = [
            GraphicElement.from_simple_dict(gd) for gd in data.get("graphics", [])
        ]

        # Recreate `units` => dict of int -> list of KicadSymbolPin
        units_raw = data.get("units", {})
        units: Dict[int, List[KicadSymbolPin]] = {}
        for unit_str, pin_list_data in units_raw.items():
            unit_int = int(unit_str)
            pins_in_unit = [KicadSymbolPin.from_simple_dict(pd) for pd in pin_list_data]
            units[unit_int] = pins_in_unit

        sym = cls(
            name=data["name"],
            reference=data.get("reference", ""),
            properties=data.get("properties", {}),
            pins=pins,
            graphics=graphics,
            units=units,
            extends=data.get("extends"),
            is_power=data.get("is_power", False),
            pin_numbers=data.get("pin_numbers"),
            pin_names_offset=data.get("pin_names_offset"),
        )
        return sym


class KicadSymbolParser:
    """Singleton parser for KiCad .kicad_sym libraries with caching."""

    _instance = None
    _initialized = False

    def __init__(self):
        self._initialized = False

    def _initialize(self):
        if self._initialized:
            return
        self._initialized = True
        logger.debug("KicadSymbolParser: Initialization complete.")

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _parse_file(self, filepath: str) -> Dict[str, KicadSymbol]:
        """
        Parse entire .kicad_sym file => dict: {symbol_name: KicadSymbol}
        Then handle 'extends' references by merging.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        try:
            sexp = sexpdata.loads(text)
        except Exception as e:
            raise ParseError(f"Cannot parse S-expression from {filepath}: {e}")

        if not isinstance(sexp, list) or not sexp:
            raise ParseError(f"Invalid top-level structure in {filepath}")

        all_symbols: Dict[str, KicadSymbol] = {}

        # pass 1: read symbol definitions
        for item in sexp[1:]:
            if (
                isinstance(item, list)
                and item
                and hasattr(item[0], "value")
                and item[0].value().lower() == "symbol"
            ):
                # item => (symbol "Name" ... )
                if len(item) < 2:
                    continue
                name = str(item[1])
                symbol_obj = self._parse_symbol_body(name, item[2:])
                all_symbols[name] = symbol_obj

        # pass 2: resolve inheritance (extends)
        self._resolve_all_extends(all_symbols)
        return all_symbols

    def _parse_symbol_body(self, name: str, body: List[Any]) -> KicadSymbol:
        """Parse the contents of a (symbol "Name" ...) block into a KicadSymbol."""
        properties: Dict[str, str] = {}
        pins: List[KicadSymbolPin] = []
        graphics: List[GraphicElement] = []
        units: Dict[int, List[KicadSymbolPin]] = {}
        extends = None
        is_power = False
        reference = ""

        # Additional KiCad symbol-level flags
        pin_numbers_mode: Optional[str] = None
        pin_names_offset: Optional[float] = None

        sub_symbols: List[List[Any]] = []

        for elem in body:
            if not isinstance(elem, list) or not elem:
                continue
            key = self._get_key(elem[0])

            if key == "property":
                # e.g. (property "Reference" "C" (at 0.635 2.54 0) (effects ...))
                self._parse_property_elem(elem, properties)
                # If property is "Reference", store local reference
                ref_key = str(elem[1]).lower() if len(elem) > 1 else ""
                val_str = str(elem[2]) if len(elem) > 2 else ""
                if ref_key == "reference":
                    reference = val_str

            elif key == "pin":
                pin_obj = self._parse_pin(elem, unit=1)
                if pin_obj:
                    pins.append(pin_obj)

            elif key == "extends":
                if len(elem) >= 2:
                    extends = str(elem[1])

            elif key == "power":
                # KiCad sometimes uses "(power)"
                is_power = True

            elif key == "pin_numbers":
                # e.g. (pin_numbers hide)
                if len(elem) >= 2:
                    pin_numbers_mode = str(elem[1])
                    logger.debug(
                        "Found pin_numbers='%s' in symbol '%s'", pin_numbers_mode, name
                    )

            elif key == "pin_names":
                # e.g. (pin_names (offset 0.254))
                # parse sub elems
                for sub_el in elem[1:]:
                    if not isinstance(sub_el, list):
                        continue
                    sub_k = self._get_key(sub_el[0])
                    if sub_k == "offset" and len(sub_el) >= 2:
                        pin_names_offset = float(sub_el[1])
                        logger.debug(
                            "Found pin_names offset=%.3f in symbol '%s'",
                            pin_names_offset,
                            name,
                        )

            elif key in ("rectangle", "circle", "arc", "polyline", "text", "bezier"):
                g = self._parse_graphic_element(elem)
                graphics.append(g)

            elif key == "symbol":
                # sub-symbol => might contain more pins/graphics
                if len(elem) >= 2:
                    sub_symbols.append(elem)

        # If we have sub-symbol blocks, parse them (they often contain pins, shapes).
        for sub_s in sub_symbols:
            child_name = str(sub_s[1])
            child_body = sub_s[2:]
            sub_pins, sub_graphics = self._parse_subsymbol(child_name, child_body)
            pins.extend(sub_pins)
            graphics.extend(sub_graphics)

            # Check unit number
            unit_num = self._get_unit_number(child_name)
            if sub_pins:
                if unit_num not in units:
                    units[unit_num] = []
                units[unit_num].extend(sub_pins)

        sym = KicadSymbol(
            name=name,
            reference=reference,
            properties=properties,
            pins=pins,
            graphics=graphics,
            units=units,
            extends=extends,
            is_power=is_power,
            pin_numbers=pin_numbers_mode,
            pin_names_offset=pin_names_offset,
        )
        logger.debug(
            "Parsed symbol '%s': reference='%s', pin_numbers=%s, pin_names_offset=%s",
            name,
            reference,
            pin_numbers_mode,
            pin_names_offset,
        )
        return sym

    def _parse_subsymbol(
        self, sub_name: str, sub_body: List[Any]
    ) -> (List[KicadSymbolPin], List[GraphicElement]):
        """Parse a child (symbol ...) block that usually holds pins, shapes, etc."""
        sub_pins: List[KicadSymbolPin] = []
        sub_graphics: List[GraphicElement] = []

        for elem in sub_body:
            if not isinstance(elem, list) or not elem:
                continue
            key = self._get_key(elem[0])

            if key == "pin":
                pin_obj = self._parse_pin(elem, unit=self._get_unit_number(sub_name))
                if pin_obj:
                    sub_pins.append(pin_obj)
            elif key in ("rectangle", "circle", "arc", "polyline", "text", "bezier"):
                g = self._parse_graphic_element(elem)
                sub_graphics.append(g)

        return sub_pins, sub_graphics

    def _parse_pin(self, pin_list: List[Any], unit: int) -> Optional[KicadSymbolPin]:
        """
        Parse a pin block, e.g.:
          (pin passive line
            (at 0 3.81 270)
            (length 1.27)
            (name "~")
            (number "1") ...)
        """
        try:
            function = "passive"
            if len(pin_list) > 1 and hasattr(pin_list[1], "value"):
                function = pin_list[1].value().lower()

            x = 0.0
            y = 0.0
            orientation = 0.0
            length = 1.27
            name = "~"
            number = ""

            # skip the first 2 tokens => 'pin' and e.g. 'passive'
            for item in pin_list[2:]:
                if not isinstance(item, list) or not item:
                    continue
                sub_key = self._get_key(item[0])
                if sub_key == "at":
                    if len(item) >= 3:
                        x = float(item[1])
                        y = float(item[2])
                    if len(item) == 4:
                        orientation = float(item[3])
                elif sub_key == "length":
                    length = float(item[1])
                elif sub_key == "name":
                    name = str(item[1])
                elif sub_key == "number":
                    number = str(item[1])

            pin_obj = KicadSymbolPin(
                pin_id=str(uuid.uuid4()),
                name=name,
                number=number,
                function=function,
                unit=unit,
                x=x,
                y=y,
                length=length,
                orientation=orientation,
            )
            logger.debug(
                "Parsed pin: name='%s', number='%s', func='%s', (x=%.2f,y=%.2f), ori=%d, length=%.2f, unit=%d",
                name,
                number,
                function,
                x,
                y,
                orientation,
                length,
                unit,
            )
            return pin_obj

        except Exception as e:
            logger.error(f"Error parsing pin: {e}")
            return None

    def _parse_graphic_element(self, elem: List[Any]) -> GraphicElement:
        """
        Parse a rectangle, circle, arc, polyline, etc.
        e.g.:
        (rectangle (start x y) (end x y) (stroke ...) (fill ...))
        (arc (start x y) (mid x y) (end x y) (stroke ...))
        """
        shape_type = self._get_key(elem[0])
        start = None
        mid = None  # Initialize midpoint
        end = None
        points = []  # Initialize points list
        radius = None  # Initialize radius
        stroke_w = 0.254
        stroke_t = "default"
        fill_t = "none"

        for sub in elem[1:]:
            if not isinstance(sub, list) or not sub:
                continue

            sub_key = self._get_key(sub[0])
            if sub_key in ("start", "center"):
                # circle uses (center x y)
                start = [float(sub[1]), float(sub[2])]
            elif sub_key == "mid":  # Extract midpoint for arcs
                mid = [float(sub[1]), float(sub[2])]
            elif sub_key == "end":
                end = [float(sub[1]), float(sub[2])]
            elif sub_key == "radius" and len(sub) > 1:  # Extract radius for circles
                radius = float(sub[1])
            elif sub_key == "pts":  # Extract points for polylines
                for pt in sub[1:]:
                    if (
                        isinstance(pt, list)
                        and len(pt) >= 3
                        and self._get_key(pt[0]) == "xy"
                    ):
                        points.append([float(pt[1]), float(pt[2])])
            elif sub_key == "stroke":
                for st_item in sub[1:]:
                    if isinstance(st_item, list) and st_item:
                        st_k = self._get_key(st_item[0])
                        if st_k == "width":
                            stroke_w = float(st_item[1])
                        elif st_k == "type":
                            stroke_t = str(st_item[1])
            elif sub_key == "fill":
                for f_item in sub[1:]:
                    if isinstance(f_item, list) and f_item:
                        f_k = self._get_key(f_item[0])
                        if f_k == "type":
                            fill_t = str(f_item[1])

        g_elem = GraphicElement(
            shape_type=shape_type,
            start=start,
            end=end,
            mid=mid,  # Include midpoint
            points=points,  # Include points
            radius=radius,  # Include radius
            stroke_width=stroke_w,
            stroke_type=stroke_t,
            fill_type=fill_t,
        )
        return g_elem

    def _parse_property_elem(self, elem: List[Any], prop_dict: Dict[str, str]) -> None:
        """
        Parse something like:
          (property "Reference" "C"
            (at 0.635 2.54 0)
            (effects (font (size 1.27 1.27)) ...)
          )
        We'll store "Reference" => "C" in prop_dict, ignoring offsets for now.
        If you want to store the offsets in prop_dict as well, you can do that here.
        """
        if len(elem) < 3:
            return
        prop_name = str(elem[1])
        prop_value = str(elem[2])

        # Store the property with both original case and lowercase key for case-insensitive access
        prop_dict[prop_name] = prop_value  # store with original case

        # For important properties like "Description", also store with a standardized lowercase key
        # This ensures tests can reliably access these properties regardless of case variations
        if prop_name.lower() == "description":
            prop_dict["description"] = prop_value
            logger.debug("Found description property: '%s'", prop_value)

        logger.debug("Found property '%s'='%s'", prop_name, prop_value)

        # If we want to parse the (at x y r) inside:
        for sub_el in elem[3:]:
            if (
                isinstance(sub_el, list)
                and sub_el
                and hasattr(sub_el[0], "value")
                and sub_el[0].value().lower() == "at"
            ):
                # e.g. (at 0.635 2.54 0)
                # For debugging/logging, you could store it in prop_dict as well:
                coords = [0.0, 0.0, 0.0]
                for i in range(1, len(sub_el)):
                    try:
                        coords[i - 1] = float(sub_el[i])
                    except ValueError:
                        pass
                logger.debug(
                    "Property '%s' has offset at=(%.3f, %.3f, %.3f)",
                    prop_name,
                    coords[0],
                    coords[1],
                    coords[2],
                )
                # Optionally store in prop_dict:
                prop_dict[f"{prop_name}_offset"] = str(coords)

    def _resolve_all_extends(self, all_symbols: Dict[str, KicadSymbol]) -> None:
        """
        For any symbol that has extends=SomeParent, merge parent's data.
        We do a small recursion to handle multi-level extends.
        """
        visited: Set[str] = set()
        for sym_name in list(all_symbols.keys()):
            self._resolve_extends_for_symbol(sym_name, all_symbols, visited)

    def _resolve_extends_for_symbol(
        self, sym_name: str, all_symbols: Dict[str, KicadSymbol], visited: Set[str]
    ) -> None:
        if sym_name in visited:
            return
        visited.add(sym_name)
        child = all_symbols[sym_name]
        parent_name = child.extends
        if parent_name and parent_name in all_symbols:
            self._resolve_extends_for_symbol(parent_name, all_symbols, visited)
            parent_obj = all_symbols[parent_name]
            child.merge_parent(parent_obj)
            child.extends = None  # fully resolved now

    def _get_unit_number(self, symbol_name: str) -> int:
        """
        Attempt to parse something like "R_0_1" => unit=0 or "R_1_1" => unit=1.
        If not found, default to 1.
        """
        parts = symbol_name.split("_")
        if len(parts) >= 3:
            try:
                return int(parts[-2])
            except ValueError:
                return 1
        return 1

    def _get_key(self, s: Any) -> str:
        """Return lowercase string of s-expression symbol."""
        if hasattr(s, "value"):
            return s.value().lower()
        return str(s).lower()

    def _find_library_file(self, lib_name: str) -> Optional[str]:
        """
        Look for 'lib_name.kicad_sym' in environment or known paths.
        If not found, return None.
        """
        kicad_dir = os.environ.get("KICAD_SYMBOL_DIR", "")
        candidates = []
        if kicad_dir:
            candidates.append(os.path.join(kicad_dir, f"{lib_name}.kicad_sym"))
        # Additional logic if desired
        for c in candidates:
            if os.path.isfile(c):
                return c
        # If you have a local dev path or fallback, you can add here
        return None

    def _find_kicad_sym_file(self, lib_name: str) -> Optional[str]:
        """
        Find the actual file path for a given library name.
        Uses the enhanced SymbolLibCache for better discovery.
        """
        # Import here to avoid circular imports
        from .kicad_symbol_cache import SymbolLibCache

        # Use the enhanced cache to find the library
        lib_path = SymbolLibCache._find_kicad_sym_file(lib_name)
        if lib_path:
            return str(lib_path)

        # Fallback to environment variable search
        kicad_dir = os.environ.get("KICAD_SYMBOL_DIR", "")
        candidates = []
        if kicad_dir:
            candidates.append(os.path.join(kicad_dir, f"{lib_name}.kicad_sym"))

        for c in candidates:
            if os.path.isfile(c):
                return c
        return None

    def parse_symbol(self, symbol_id: str) -> KicadSymbol:
        """
        Parse a specific symbol by ID (LibName:SymbolName).
        This method is called by the preparse script to cache symbols.
        """
        try:
            lib_name, sym_name = symbol_id.split(":")
        except ValueError:
            raise ValueError(
                f"Invalid symbol_id format; expected 'LibName:SymbolName', got '{symbol_id}'"
            )

        # Find the library file
        lib_path = self._find_kicad_sym_file(lib_name)
        if not lib_path:
            raise LibraryNotFound(f"Could not find .kicad_sym for library '{lib_name}'")

        # Parse the entire library file
        all_symbols = self._parse_file(lib_path)

        # Return the specific symbol
        if sym_name not in all_symbols:
            raise SymbolNotFoundError(
                f"Symbol '{sym_name}' not found in library '{lib_name}'"
            )

        return all_symbols[sym_name]
