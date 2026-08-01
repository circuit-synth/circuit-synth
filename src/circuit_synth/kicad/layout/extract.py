# -*- coding: utf-8 -*-
"""Describe a generated sheet so a layout can be reasoned about.

Placing a schematic well needs more than a netlist. It needs to know where each
pin sits on its symbol and which way it faces, because that is what decides
which way round a part should go and where a wire can leave it. This module
gathers that, per sheet, into one description.
"""

import json
import logging
import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import sexp

logger = logging.getLogger(__name__)


@dataclass
class PinDescription:
    """One pin of a placed symbol.

    Attributes:
        number: Pin number as KiCad knows it.
        name: Pin name from the symbol library.
        electrical_type: KiCad pin type, such as ``"power_in"`` or ``"output"``.
        offset: Pin position relative to the symbol origin, in schematic mm,
            with the symbol unrotated.
        side: Which side of the body the pin leaves from, once rotation is
            applied: ``"left"``, ``"right"``, ``"top"`` or ``"bottom"``.
        net: The net attached to this pin, or None.
    """

    number: str
    name: str
    electrical_type: str
    offset: Tuple[float, float]
    side: str
    net: Optional[str] = None


@dataclass
class ComponentDescription:
    """One placed symbol.

    Attributes:
        reference: Reference designator.
        value: Value field.
        lib_id: Library identifier.
        position: Current ``(x, y)`` origin in mm.
        rotation: Current rotation in degrees.
        body: Symbol body size as ``(width, height)`` in mm, excluding text.
        pins: The symbol's pins.
        is_power: Whether this is a power symbol rather than a real part.
    """

    reference: str
    value: str
    lib_id: str
    position: Tuple[float, float]
    rotation: float
    body: Tuple[float, float]
    pins: List[PinDescription] = field(default_factory=list)
    is_power: bool = False


@dataclass
class SheetDescription:
    """Everything needed to lay out one sheet.

    Attributes:
        path: Path to the .kicad_sch file.
        name: Sheet name.
        paper: Paper size, such as ``"A4"``.
        extents: Usable drawing area as ``(min_x, min_y, max_x, max_y)`` in mm.
        components: The real parts on the sheet.
        power_symbols: The power symbols on the sheet.
        nets: Net name to the ``"REF.PIN"`` tokens on it.
        ports: Hierarchical port name to direction, for a sheet that is a block.
        child_sheets: Names of the sheet symbols placed on this sheet.
    """

    path: str
    name: str
    paper: str
    extents: Tuple[float, float, float, float]
    components: List[ComponentDescription] = field(default_factory=list)
    power_symbols: List[ComponentDescription] = field(default_factory=list)
    nets: Dict[str, List[str]] = field(default_factory=dict)
    ports: Dict[str, str] = field(default_factory=dict)
    child_sheets: List[str] = field(default_factory=list)

    def to_json(self, indent: int = 1) -> str:
        """Serialize the description.

        Args:
            indent: JSON indentation.

        Returns:
            The description as JSON.
        """
        return json.dumps(asdict(self), indent=indent)


# Usable area per paper size, in mm, inside KiCad's drawing frame.
PAPER_EXTENTS = {
    "A4": (12.7, 12.7, 284.0, 197.0),
    "A3": (12.7, 12.7, 407.0, 284.0),
    "A2": (12.7, 12.7, 581.0, 407.0),
}


def _pin_side(offset: Tuple[float, float], rotation: float) -> str:
    """Work out which way a pin faces once its symbol is rotated.

    Args:
        offset: The pin's offset from the symbol origin, unrotated.
        rotation: The symbol's rotation in degrees.

    Returns:
        ``"left"``, ``"right"``, ``"top"`` or ``"bottom"``.
    """
    radians = math.radians(-rotation)
    x = offset[0] * math.cos(radians) - offset[1] * math.sin(radians)
    y = offset[0] * math.sin(radians) + offset[1] * math.cos(radians)
    if abs(x) >= abs(y):
        return "right" if x > 0 else "left"
    return "bottom" if y > 0 else "top"


def describe_sheet(
    sheet_path: Path,
    nets: Optional[Dict[str, List[str]]] = None,
    ports: Optional[Dict[str, str]] = None,
) -> SheetDescription:
    """Read a sheet and describe what is on it.

    Args:
        sheet_path: Path to the .kicad_sch file.
        nets: Net name to ``"REF.PIN"`` tokens for this sheet, when known.
        ports: Hierarchical port name to direction, when the sheet is a block.

    Returns:
        The sheet description.
    """
    from ..kicad_symbol_cache import SymbolLibCache
    from ..sch_gen.symbol_geometry import SymbolBoundingBoxCalculator
    from ..sch_gen.wired_layout import rotate_offset

    text = sheet_path.read_text(encoding="utf-8")
    paper = sexp.read_string(text, "paper") or "A4"

    pin_nets: Dict[str, str] = {}
    for net_name, tokens in (nets or {}).items():
        for token in tokens:
            pin_nets[token] = net_name

    components: List[ComponentDescription] = []
    power_symbols: List[ComponentDescription] = []

    for extent in sexp.iter_blocks(text, "symbol"):
        block = sexp.block_text(text, extent)
        lib_id = sexp.read_string(block, "lib_id")
        position = sexp.read_position(block)
        reference = sexp.read_property(block, "Reference")
        if not lib_id or position is None or not reference:
            continue

        value = sexp.read_property(block, "Value") or ""
        is_power = lib_id.startswith("power:")

        pins: List[PinDescription] = []
        body = (10.0, 10.0)
        try:
            lib_data = SymbolLibCache.get_symbol_data(lib_id)
        except Exception as error:  # pragma: no cover - library lookup varies
            logger.debug("No library data for %s: %s", lib_id, error)
            lib_data = None

        if lib_data:
            try:
                body = SymbolBoundingBoxCalculator.get_symbol_dimensions(
                    lib_data, include_properties=False
                )
            except Exception:  # pragma: no cover - defensive
                body = (10.0, 10.0)

            for pin_data in lib_data.get("pins", []):
                number = str(pin_data.get("number", ""))
                offset = rotate_offset(
                    float(pin_data.get("x", 0.0)), float(pin_data.get("y", 0.0)), 0.0
                )
                pins.append(
                    PinDescription(
                        number=number,
                        name=pin_data.get("name", ""),
                        electrical_type=pin_data.get("function")
                        or pin_data.get("func", "passive"),
                        offset=(round(offset[0], 3), round(offset[1], 3)),
                        side=_pin_side(offset, position[2]),
                        net=pin_nets.get(f"{reference}.{number}"),
                    )
                )

        description = ComponentDescription(
            reference=reference,
            value=value,
            lib_id=lib_id,
            position=(position[0], position[1]),
            rotation=position[2],
            body=(round(body[0], 2), round(body[1], 2)),
            pins=pins,
            is_power=is_power,
        )
        (power_symbols if is_power else components).append(description)

    child_sheets = re.findall(r'\(property "Sheetname" "([^"]+)"', text)

    return SheetDescription(
        path=str(sheet_path),
        name=sheet_path.stem,
        paper=paper,
        extents=PAPER_EXTENTS.get(paper, PAPER_EXTENTS["A4"]),
        components=components,
        power_symbols=power_symbols,
        nets=nets or {},
        ports=ports or {},
        child_sheets=child_sheets,
    )


def sheet_nets(circuit_json: Path) -> Dict[str, Dict[str, List[str]]]:
    """Read the per-sheet nets out of a generated circuit JSON.

    Args:
        circuit_json: The generated circuit JSON.

    Returns:
        Sheet name to a mapping of net name to ``"REF.PIN"`` tokens. The root
        circuit is keyed by its own name.
    """
    data = json.loads(circuit_json.read_text(encoding="utf-8"))
    result: Dict[str, Dict[str, List[str]]] = {}

    def walk(node: dict) -> None:
        name = node.get("name", "")
        nets: Dict[str, List[str]] = {}
        for net_name, info in (node.get("nets") or {}).items():
            entries = info.get("nodes", info) if isinstance(info, dict) else info
            nets[net_name] = [
                f"{entry['component']}.{entry['pin']['number']}" for entry in entries
            ]
        # Repeated instances of one block are written to separate sheets whose
        # names gain a numeric suffix, so keep every instance seen.
        candidate = name
        suffix = 2
        while candidate in result:
            candidate = f"{name}{suffix}"
            suffix += 1
        result[candidate] = nets

        for child in node.get("subcircuits") or []:
            walk(child)

    walk(data)
    return result


def sheet_ports(circuit_json: Path) -> Dict[str, Dict[str, str]]:
    """Read the declared hierarchical ports of each block from a circuit JSON.

    Args:
        circuit_json: The generated circuit JSON.

    Returns:
        Sheet name to a mapping of port name to direction.
    """
    data = json.loads(circuit_json.read_text(encoding="utf-8"))
    result: Dict[str, Dict[str, str]] = {}

    def walk(node: dict) -> None:
        name = node.get("name", "")
        candidate = name
        suffix = 2
        while candidate in result:
            candidate = f"{name}{suffix}"
            suffix += 1
        result[candidate] = {
            port["name"]: port["direction"] for port in (node.get("ports") or [])
        }
        for child in node.get("subcircuits") or []:
            walk(child)

    walk(data)
    return result
