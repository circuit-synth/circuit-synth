# -*- coding: utf-8 -*-
"""Apply a placement decision to a generated sheet.

A placement spec says where each part goes and how the sheet is wired. Applying
it moves the symbols and redraws the wiring, and leaves everything else in the
file untouched: the symbol library, the component UUIDs, the property text and
the hierarchical instance paths all survive, so the sheet stays the same design
and only its drawing changes.
"""

import json
import logging
import re
import uuid as uuid_module
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from . import sexp

logger = logging.getLogger(__name__)

Point = Tuple[float, float]
GRID = 1.27


@dataclass
class ComponentPlacement:
    """Where one symbol goes.

    Attributes:
        reference: Reference designator of the symbol to move.
        at: New ``(x, y)`` origin in mm.
        rotation: New rotation in degrees, or None to keep the current one.
    """

    reference: str
    at: Point
    rotation: Optional[float] = None


@dataclass
class LabelPlacement:
    """A net label.

    Attributes:
        text: The label text, which is what decides connectivity.
        at: The ``(x, y)`` anchor, which must sit on a wire end or a pin.
        rotation: Direction the text runs, in degrees.
        kind: ``"local"``, ``"hierarchical"`` or ``"global"``.
        shape: Hierarchical label shape, such as ``"input"``.
    """

    text: str
    at: Point
    rotation: float = 0.0
    kind: str = "local"
    shape: str = "input"


@dataclass
class PowerPlacement:
    """A power symbol.

    Attributes:
        lib_id: Library id, such as ``"power:GND"``.
        at: The ``(x, y)`` connection point.
        rotation: Symbol rotation in degrees.
        reference: Reference designator, assigned automatically when omitted.
    """

    lib_id: str
    at: Point
    rotation: float = 0.0
    reference: Optional[str] = None


@dataclass
class PlacementSpec:
    """A complete placement for one sheet.

    Attributes:
        components: Where each real part goes.
        wires: Wire segments as ``(start, end)`` point pairs.
        junctions: Points where three or more connections meet.
        labels: Net labels.
        power: Power symbols.
        no_connects: Points marked as intentionally unconnected.
    """

    components: List[ComponentPlacement] = field(default_factory=list)
    wires: List[Tuple[Point, Point]] = field(default_factory=list)
    junctions: List[Point] = field(default_factory=list)
    labels: List[LabelPlacement] = field(default_factory=list)
    power: List[PowerPlacement] = field(default_factory=list)
    no_connects: List[Point] = field(default_factory=list)
    paper: Optional[str] = None

    def translated(self, dx: float, dy: float) -> "PlacementSpec":
        """Return the same placement moved bodily across the sheet.

        Useful for centring a finished layout on its page without redoing every
        coordinate by hand.

        Args:
            dx: Distance to move in x, in mm.
            dy: Distance to move in y, in mm.

        Returns:
            A new spec with every coordinate shifted.
        """
        move = lambda point: (round(point[0] + dx, 4), round(point[1] + dy, 4))
        return PlacementSpec(
            components=[
                ComponentPlacement(item.reference, move(item.at), item.rotation)
                for item in self.components
            ],
            wires=[(move(start), move(end)) for start, end in self.wires],
            junctions=[move(point) for point in self.junctions],
            labels=[
                LabelPlacement(
                    item.text, move(item.at), item.rotation, item.kind, item.shape
                )
                for item in self.labels
            ],
            power=[
                PowerPlacement(item.lib_id, move(item.at), item.rotation, item.reference)
                for item in self.power
            ],
            no_connects=[move(point) for point in self.no_connects],
            paper=self.paper,
        )

    def renamed(self, mapping: Dict[str, str]) -> "PlacementSpec":
        """Return the same placement applied to a different set of references.

        Two instances of one block have the same shape and different reference
        designators, so a layout written for one can be reused for the others.

        Args:
            mapping: Old reference to new reference.

        Returns:
            A new spec addressing the renamed components.
        """
        renamed = PlacementSpec(
            components=[
                ComponentPlacement(
                    mapping.get(item.reference, item.reference), item.at, item.rotation
                )
                for item in self.components
            ],
            wires=list(self.wires),
            junctions=list(self.junctions),
            labels=list(self.labels),
            power=list(self.power),
            no_connects=list(self.no_connects),
            paper=self.paper,
        )
        return renamed

    @staticmethod
    def from_dict(data: dict) -> "PlacementSpec":
        """Build a spec from plain data, as read from JSON.

        Args:
            data: The spec as nested dictionaries and lists.

        Returns:
            The parsed spec.
        """
        return PlacementSpec(
            components=[
                ComponentPlacement(
                    reference=entry["ref"],
                    at=tuple(entry["at"]),
                    rotation=entry.get("rotation"),
                )
                for entry in data.get("components", [])
            ],
            wires=[
                (tuple(segment[0]), tuple(segment[1]))
                for segment in data.get("wires", [])
            ],
            junctions=[tuple(point) for point in data.get("junctions", [])],
            labels=[
                LabelPlacement(
                    text=entry["text"],
                    at=tuple(entry["at"]),
                    rotation=float(entry.get("rotation", 0.0)),
                    kind=entry.get("kind", "local"),
                    shape=entry.get("shape", "input"),
                )
                for entry in data.get("labels", [])
            ],
            power=[
                PowerPlacement(
                    lib_id=entry["lib_id"],
                    at=tuple(entry["at"]),
                    rotation=float(entry.get("rotation", 0.0)),
                    reference=entry.get("reference"),
                )
                for entry in data.get("power", [])
            ],
            no_connects=[tuple(point) for point in data.get("no_connects", [])],
            paper=data.get("paper"),
        )

    @staticmethod
    def from_json(path: Path) -> "PlacementSpec":
        """Read a spec from a JSON file.

        Args:
            path: Path to the JSON file.

        Returns:
            The parsed spec.
        """
        return PlacementSpec.from_dict(json.loads(path.read_text(encoding="utf-8")))


def _off_grid(points: Sequence[Point]) -> List[Point]:
    """List the points that do not sit on KiCad's grid.

    Args:
        points: The points to check.

    Returns:
        The offending points.
    """
    bad = []
    for x, y in points:
        if (
            abs(x / GRID - round(x / GRID)) > 1e-6
            or abs(y / GRID - round(y / GRID)) > 1e-6
        ):
            bad.append((x, y))
    return bad


def _wire_sexp(start: Point, end: Point) -> str:
    """Render a wire segment.

    Args:
        start: One end point.
        end: The other end point.

    Returns:
        The S-expression text.
    """
    return (
        f"\n\t(wire\n\t\t(pts\n\t\t\t(xy {start[0]:g} {start[1]:g})"
        f" (xy {end[0]:g} {end[1]:g})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)"
        f'\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{uuid_module.uuid4()}")\n\t)'
    )


def _junction_sexp(point: Point) -> str:
    """Render a junction dot.

    Args:
        point: Where the connections meet.

    Returns:
        The S-expression text.
    """
    return (
        f"\n\t(junction\n\t\t(at {point[0]:g} {point[1]:g})\n\t\t(diameter 0)"
        f'\n\t\t(color 0 0 0 0)\n\t\t(uuid "{uuid_module.uuid4()}")\n\t)'
    )


def _no_connect_sexp(point: Point) -> str:
    """Render a no-connect marker.

    Args:
        point: The pin left unconnected.

    Returns:
        The S-expression text.
    """
    return (
        f"\n\t(no_connect\n\t\t(at {point[0]:g} {point[1]:g})"
        f'\n\t\t(uuid "{uuid_module.uuid4()}")\n\t)'
    )


def _justify(rotation: float) -> str:
    """Choose text justification for a label's direction.

    Args:
        rotation: The label rotation in degrees.

    Returns:
        ``"left"`` or ``"right"``.
    """
    return "left" if round(rotation) % 360 in (0, 90) else "right"


def _label_sexp(label: LabelPlacement) -> str:
    """Render a net label.

    Args:
        label: The label to draw.

    Returns:
        The S-expression text.
    """
    keyword = {
        "local": "label",
        "hierarchical": "hierarchical_label",
        "global": "global_label",
    }[label.kind]

    shape = ""
    if label.kind == "hierarchical":
        shape = f"\n\t\t(shape {label.shape})"

    return (
        f'\n\t({keyword} "{label.text}"{shape}'
        f"\n\t\t(at {label.at[0]:g} {label.at[1]:g} {label.rotation:g})"
        f"\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)"
        f"\n\t\t\t(justify {_justify(label.rotation)})\n\t\t)"
        f'\n\t\t(uuid "{uuid_module.uuid4()}")\n\t)'
    )


def _power_sexp(power: PowerPlacement, reference: str, project: str) -> str:
    """Render a power symbol.

    Args:
        power: The symbol to draw.
        reference: Reference designator to give it.
        project: Project name for the instance path.

    Returns:
        The S-expression text.
    """
    x, y = power.at
    value = power.lib_id.split(":", 1)[-1]
    # The rail name reads best just beyond the symbol, on the side it points.
    text_y = y + 5.08 if round(power.rotation) % 360 == 0 else y - 5.08
    return (
        f'\n\t(symbol\n\t\t(lib_id "{power.lib_id}")'
        f"\n\t\t(at {x:g} {y:g} {power.rotation:g})\n\t\t(unit 1)"
        f"\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)"
        f"\n\t\t(dnp no)\n\t\t(fields_autoplaced no)"
        f'\n\t\t(uuid "{uuid_module.uuid4()}")'
        f'\n\t\t(property "Reference" "{reference}"'
        f"\n\t\t\t(at {x:g} {y - 6.35:g} 0)\n\t\t\t(effects\n\t\t\t\t(font"
        f"\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(hide yes)\n\t\t\t)\n\t\t)"
        f'\n\t\t(property "Value" "{value}"'
        f"\n\t\t\t(at {x:g} {text_y:g} 0)\n\t\t\t(effects\n\t\t\t\t(font"
        f"\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)"
        f'\n\t\t(property "Footprint" ""'
        f"\n\t\t\t(at {x:g} {y:g} 0)\n\t\t\t(effects\n\t\t\t\t(font"
        f"\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(hide yes)\n\t\t\t)\n\t\t)"
        f'\n\t\t(pin "1"\n\t\t\t(uuid "{uuid_module.uuid4()}")\n\t\t)'
        f'\n\t\t(instances\n\t\t\t(project "{project}"\n\t\t\t\t(path "/"'
        f'\n\t\t\t\t\t(reference "{reference}")\n\t\t\t\t\t(unit 1)'
        f"\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)"
    )


def apply_placement(
    sheet_path: Path, spec: PlacementSpec, snap_to_grid: bool = True
) -> Dict[str, int]:
    """Apply a placement spec to a sheet in place.

    Args:
        sheet_path: The .kicad_sch to rewrite.
        spec: The placement to apply.
        snap_to_grid: Reject coordinates that are not on KiCad's grid. Wires
            that miss a pin by a fraction of a millimetre look connected and
            are not, so this is on by default.

    Returns:
        Counts of what was written, keyed by element kind.

    Raises:
        ValueError: If the spec names a component the sheet does not have, or
            uses coordinates off the grid while ``snap_to_grid`` is set.
    """
    text = sheet_path.read_text(encoding="utf-8")

    if snap_to_grid:
        points: List[Point] = [placement.at for placement in spec.components]
        points += [point for segment in spec.wires for point in segment]
        points += list(spec.junctions)
        points += [label.at for label in spec.labels]
        points += [power.at for power in spec.power]
        off = _off_grid(points)
        if off:
            raise ValueError(
                f"{len(off)} coordinate(s) are not on the {GRID}mm grid, "
                f"first is {off[0]}"
            )

    project = ""
    match = re.search(r'\(project "([^"]*)"', text)
    if match:
        project = match.group(1)

    if spec.paper:
        text = re.sub(r'\(paper "[^"]*"\)', f'(paper "{spec.paper}")', text, count=1)

    # Move the real parts. Power symbols are redrawn from the spec instead, so
    # they are removed here and written back below.
    wanted = {placement.reference: placement for placement in spec.components}
    moved = 0

    # Rewriting a block changes the length of the text after it, so the blocks
    # are edited back to front and the offsets in front of the edit stay valid.
    for extent in sorted(sexp.iter_blocks(text, "symbol"), reverse=True):
        block = sexp.block_text(text, extent)
        lib_id = sexp.read_string(block, "lib_id") or ""
        if lib_id.startswith("power:"):
            continue

        reference = sexp.read_property(block, "Reference")
        placement = wanted.pop(reference, None)
        if placement is None:
            continue

        position = sexp.read_position(block)
        if position is None:
            continue
        updated = sexp.replace_positions(
            block,
            placement.at[0] - position[0],
            placement.at[1] - position[1],
            placement.rotation,
        )
        text = text[: extent[0]] + updated + text[extent[1] :]
        moved += 1

    if wanted:
        raise ValueError(
            f"sheet {sheet_path.name} has no component(s) named " f"{sorted(wanted)}"
        )

    # Replace all of the drawing. Everything here is generated from the spec,
    # so nothing is lost by clearing it first.
    text = sexp.strip_blocks(
        text,
        [
            "wire",
            "junction",
            "label",
            "hierarchical_label",
            "global_label",
            "no_connect",
        ],
    )
    for start, end in sorted(
        (
            extent
            for extent in sexp.iter_blocks(text, "symbol")
            if (
                sexp.read_string(sexp.block_text(text, extent), "lib_id") or ""
            ).startswith("power:")
        ),
        reverse=True,
    ):
        line_start = text.rfind("\n", 0, start)
        text = text[:line_start] + text[end:]

    additions = []
    for start, end in spec.wires:
        additions.append(_wire_sexp(start, end))
    for point in spec.junctions:
        additions.append(_junction_sexp(point))
    for point in spec.no_connects:
        additions.append(_no_connect_sexp(point))
    for label in spec.labels:
        additions.append(_label_sexp(label))
    for index, power in enumerate(spec.power, start=1):
        reference = power.reference or f"#PWR{index:03d}"
        additions.append(_power_sexp(power, reference, project))

    text = sexp.insert_before_end(text, "".join(additions))
    sheet_path.write_text(text, encoding="utf-8")

    written = {
        "components_moved": moved,
        "wires": len(spec.wires),
        "junctions": len(spec.junctions),
        "labels": len(spec.labels),
        "power_symbols": len(spec.power),
        "no_connects": len(spec.no_connects),
    }
    logger.info("Applied placement to %s: %s", sheet_path.name, written)
    return written
