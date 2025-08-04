"""
kicad_symbol_parser.py

Parses a KiCad .kicad_sym library file and returns a dictionary of flattened symbol data.
Handles "extends" inheritance by merging parent symbol data into the child.
"""

import logging
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import sexpdata

# Add performance timing
try:
    from ..core.performance_profiler import quick_time
except ImportError:
    # Fallback if profiler not available
    def quick_time(name):
        def decorator(func):
            return func

        return decorator


logger = logging.getLogger(__name__)

# Enable debug logging for this module
logger.setLevel(logging.DEBUG)


class ParseError(Exception):
    pass


@quick_time("KiCad Symbol File Parse")
def parse_kicad_sym_file(file_path: str) -> Dict[str, Any]:
    """
    Parse an entire .kicad_sym file and return a dictionary:
      {
          "symbols": {
              "SymbolName": { ... flattened data ... },
              "OtherSymbol": { ... },
              ...
          }
      }

    The dictionary is JSON-serializable. Each symbol has the child's data plus
    any inherited fields if (extends "ParentSymbolName") is used.
    """

    # 1) Read file
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"No such file: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        raise ParseError(f"Failed to read file: {file_path}, error={e}") from e

    # 2) Parse as S-expressions
    try:
        sexp = sexpdata.loads(text)
    except Exception as e:
        raise ParseError(f"Cannot parse S-expression from {file_path}: {e}") from e

    # Expect top-level: (kicad_symbol_lib (version ...) (symbol "Name" ...) ...)
    if not isinstance(sexp, list) or not sexp:
        raise ParseError(f"Invalid top-level structure in {file_path}")

    # 3) Gather all symbol blocks
    # Typically sexp[0] is Symbol('kicad_symbol_lib'), so the rest are library items
    # We'll store partial data in a dict: {symbol_name: { "extends": ... "properties": ... } }
    library_dict: Dict[str, Any] = {}

    for item in sexp[1:]:
        if not isinstance(item, list) or len(item) < 2:
            continue

        # item might be: (symbol "Ammeter_AC" (pin_numbers ...) (property ...) ...)
        # The first element item[0] should be Symbol('symbol') if it’s a symbol block
        if _key(item[0]) == "symbol":
            # second element is the symbol name, e.g. "Ammeter_AC"
            sym_name = str(item[1])
            # parse the rest as the symbol body
            sym_data = _parse_symbol_body(sym_name, item[2:])
            library_dict[sym_name] = sym_data

    # 4) Resolve extends (inheritance). If AMS1117-3.3 extends AP1117-15,
    # we copy the parent's pins/graphics into the child if not present
    _resolve_extends_in_library(library_dict)

    # 5) Flatten symbols to JSON-friendly dictionaries
    # We store them in "symbols" sub-dict
    flattened_symbols = {}
    for name, data in library_dict.items():
        flattened_symbols[name] = _flatten_symbol(name, data, library_dict)

    return {"symbols": flattened_symbols}


def _parse_symbol_body(name: str, body: List[Any]) -> Dict[str, Any]:
    """
    Given an s-expression list for a (symbol "Name" ... ), parse out properties,
    pins, sub-symbol blocks, etc. Return partial dictionary with possible "extends".
    We do NOT handle merging yet; that’s done later.
    """

    result: Dict[str, Any] = {
        "name": name,
        "extends": None,
        "properties": {},  # map property_name -> string (generic storage)
        "description": None,  # Specific field for Description property
        "datasheet": None,  # Specific field for Datasheet property
        "keywords": None,  # Specific field for Keywords property
        "fp_filters": None,  # Specific field for ki_fp_filters property
        "graphics": [],  # list of shapes
        "pins": [],  # list of pin definitions
        "sub_symbols": [],  # sub-symbol blocks (like name_0_1)
        "is_power": False,
    }

    for elem in body:
        if not isinstance(elem, list) or not elem:
            continue

        k = _key(elem[0])
        if k == "property":
            # (property "Reference" "R" (at ...) (effects ...))
            if len(elem) >= 3:
                prop_name = str(elem[1])
                prop_value = str(elem[2])
                # Store generically
                result["properties"][prop_name] = prop_value
                # Also store specific standard properties directly
                prop_name_lower = prop_name.lower()
                if prop_name_lower == "description":
                    result["description"] = prop_value
                elif prop_name_lower == "datasheet":
                    result["datasheet"] = prop_value
                elif prop_name_lower == "keywords":
                    result["keywords"] = prop_value
                elif prop_name_lower == "ki_fp_filters":  # KiCad standard name
                    result["fp_filters"] = prop_value

        elif k == "extends":
            if len(elem) >= 2:
                result["extends"] = str(elem[1])

        elif k == "pin":
            # parse a single pin block
            pin_data = _parse_pin(elem)
            if pin_data:
                result["pins"].append(pin_data)

        elif k == "power":
            # e.g. (power)
            result["is_power"] = True

        elif k in ("rectangle", "circle", "arc", "polyline", "text", "bezier"):
            shape = _parse_graphic_element(elem)
            if shape:
                result["graphics"].append(shape)

        elif k == "symbol":
            # This is a sub-symbol block, e.g. (symbol "Ammeter_AC_0_1" ...)
            # We’ll parse it separately, store in sub_symbols, then we can combine
            # pins/graphics. Typically these are “units.”
            if len(elem) >= 2:
                child_sym_name = str(elem[1])
                child_body = elem[2:]
                sub_sym_data = _parse_subsymbol(child_sym_name, child_body)
                result["sub_symbols"].append(sub_sym_data)

    return result


def _parse_subsymbol(sub_name: str, body: List[Any]) -> Dict[str, Any]:
    """
    Sub-symbol blocks often contain additional pins or shapes.
    Example: (symbol "Ammeter_AC_0_1" (pin ...) (arc ...) (rectangle ...) ...)
    """
    sub_data = {"sub_name": sub_name, "pins": [], "graphics": []}
    for e in body:
        if not isinstance(e, list) or not e:
            continue
        k = _key(e[0])
        if k == "pin":
            pin_data = _parse_pin(e)
            if pin_data:
                sub_data["pins"].append(pin_data)
        elif k in ("rectangle", "circle", "arc", "polyline", "text", "bezier"):
            shape = _parse_graphic_element(e)
            if shape:
                sub_data["graphics"].append(shape)
    return sub_data


def _parse_pin(pin_list: List[Any]) -> Optional[Dict[str, Any]]:
    """
    Parse a (pin function line (at x y orientation) (length ...) (name ...) (number ...))
    Return dictionary with pin function, name, number, x, y, orientation, length, etc.
    """
    try:
        pin_func = "passive"
        if len(pin_list) > 1 and hasattr(pin_list[1], "value"):
            pin_func = pin_list[1].value().lower()

        x = 0.0
        y = 0.0
        orientation = 0.0
        length = 2.54
        pin_name = "~"
        pin_number = ""

        # skip "pin" and <function> => start from pin_list[2:]
        for item in pin_list[2:]:
            if not isinstance(item, list) or not item:
                continue
            sub_k = _key(item[0])
            if sub_k == "at":
                if len(item) >= 3:
                    x = float(item[1])
                    y = float(item[2])
                if len(item) == 4:
                    orientation = float(item[3])
            elif sub_k == "length":
                length = float(item[1])
            elif sub_k == "name":
                pin_name = str(item[1])
            elif sub_k == "number":
                pin_number = str(item[1])

        return {
            "function": pin_func,
            "name": pin_name,
            "number": pin_number,
            "x": x,
            "y": y,
            "orientation": orientation,
            "length": length,
        }
    except Exception as e:
        logger.warning(f"Error parsing pin: {e}")
        return None


def _parse_graphic_element(elem: List[Any]) -> Dict[str, Any]:
    """
    Convert a shape like (rectangle (start x y) (end x y) (stroke ...) (fill ...)) or arcs, circles, etc.
    into a dictionary with shape_type, start, end, stroke_width, stroke_type, fill_type, etc.
    """
    shape_type = _key(elem[0])
    shape_data = {
        "shape_type": shape_type,
        "points": [],  # for polyline or arcs
        "start": None,
        "end": None,
        "center": None,  # for circles
        "radius": None,  # for circles
        "stroke_width": 0.254,
        "stroke_type": "default",
        "fill_type": "none",
    }

    # parse subitems
    for sub in elem[1:]:
        if not isinstance(sub, list) or not sub:
            continue
        sk = _key(sub[0])
        if sk == "start":
            if len(sub) >= 3:
                shape_data["start"] = [float(sub[1]), float(sub[2])]
        elif sk == "center":
            # For circles, store center separately
            if len(sub) >= 3:
                shape_data["center"] = [float(sub[1]), float(sub[2])]
        elif sk == "end":
            if len(sub) >= 3:
                shape_data["end"] = [float(sub[1]), float(sub[2])]
        elif sk == "mid":
            # Handle arc midpoint
            if len(sub) >= 3:
                shape_data["mid"] = [float(sub[1]), float(sub[2])]
        elif sk == "radius":
            # Handle circle radius
            if len(sub) >= 2:
                shape_data["radius"] = float(sub[1])
        elif sk == "pts":
            # For (polyline (pts (xy x y) (xy x y) ...))
            # or arc might also have (mid ...)? We'll store the points in a list
            # This is a very simplified approach
            points = []
            for p in sub[1:]:
                if isinstance(p, list) and len(p) == 3 and _key(p[0]) == "xy":
                    px = float(p[1])
                    py = float(p[2])
                    points.append((px, py))
            shape_data["points"] = points
        elif sk == "stroke":
            # read (stroke (width 0.254) (type default))
            for st_item in sub[1:]:
                if isinstance(st_item, list) and len(st_item) >= 2:
                    st_k = _key(st_item[0])
                    if st_k == "width":
                        shape_data["stroke_width"] = float(st_item[1])
                    elif st_k == "type":
                        shape_data["stroke_type"] = str(st_item[1])
        elif sk == "fill":
            # (fill (type none)) or (fill (type background))
            for f_item in sub[1:]:
                if isinstance(f_item, list) and len(f_item) >= 2:
                    f_k = _key(f_item[0])
                    if f_k == "type":
                        shape_data["fill_type"] = str(f_item[1])
    return shape_data


def _resolve_extends_in_library(library_dict: Dict[str, Any]) -> None:
    """
    For any symbol that has extends=Parent, merge parent's data recursively.
    Child overrides where it has data; any missing data is inherited.
    """
    visited: Set[str] = set()
    for sym_name in list(library_dict.keys()):
        _resolve_symbol_extends(sym_name, library_dict, visited)


def _resolve_symbol_extends(
    sym_name: str, library_dict: Dict[str, Any], visited: Set[str]
) -> None:
    if sym_name in visited:
        return
    visited.add(sym_name)

    child_data = library_dict[sym_name]
    parent_name = child_data.get("extends")
    if not parent_name:
        return
    # If the parent is in the library:
    if parent_name in library_dict:
        # recursively ensure the parent is resolved
        _resolve_symbol_extends(parent_name, library_dict, visited)
        parent_data = library_dict[parent_name]
        _merge_parent_into_child(child_data, parent_data)
        # set extends=None because now it's resolved
        child_data["extends"] = None


def _merge_parent_into_child(child: Dict[str, Any], parent: Dict[str, Any]) -> None:
    """
    Merge parent's properties, pins, sub_symbols, graphics into child if child does not override them.
    For example, if child has no pins, we take parent's pins.
    If child has some pins, we can optionally combine them.
    (Exact rules can vary by your preference.)
    """
    # Merge properties
    for k, v in parent.get("properties", {}).items():
        if k not in child["properties"]:
            child["properties"][k] = v

    # Merge pins
    if not child["pins"] and parent["pins"]:
        child["pins"] = deepcopy(parent["pins"])

    # Merge graphics
    if not child["graphics"] and parent["graphics"]:
        child["graphics"] = deepcopy(parent["graphics"])

    # Merge sub_symbols
    if not child["sub_symbols"] and parent["sub_symbols"]:
        child["sub_symbols"] = deepcopy(parent["sub_symbols"])

    # If parent is power, child is also power
    if parent.get("is_power"):
        child["is_power"] = True


def _flatten_symbol(
    sym_name: str, sym_data: Dict[str, Any], library_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Turn the final, merged data for a symbol into a JSON-serializable dict
    with shape:
      {
        "name": ...,
        "properties": {...},
        "pins": [...],
        "graphics": [...],
        "is_power": bool
      }

    Also merges in sub_symbols’ pins/graphics.
    """
    # gather all pins
    pins = list(sym_data["pins"])
    graphics = list(sym_data["graphics"])

    # Add sub_symbols pins/graphics
    for sub_s in sym_data.get("sub_symbols", []):
        pins.extend(sub_s["pins"])
        graphics.extend(sub_s["graphics"])

    return {
        "name": sym_name,
        "properties": sym_data["properties"],
        "description": sym_data["description"],
        "datasheet": sym_data["datasheet"],
        "keywords": sym_data["keywords"],
        "fp_filters": sym_data["fp_filters"],
        "pins": pins,
        "graphics": graphics,
        "is_power": sym_data["is_power"],
    }


def _key(obj: Any) -> str:
    """
    Safely convert a sexpdata.Symbol or string to lower-case string.
    """
    if hasattr(obj, "value"):
        return obj.value().lower()
    return str(obj).lower()
