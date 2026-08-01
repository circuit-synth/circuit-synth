"""Unit tests for the wired schematic layout.

Covers the layout engine's geometry helpers and the schematic it produces for a
small filter: parts placed on an even pitch, wires drawn between them, a
junction where three connections meet, and a power symbol for ground.
"""

import re
import shutil
import tempfile
from pathlib import Path
from typing import List, Tuple

import pytest

from circuit_synth import Component, Input, Net, Output, circuit
from circuit_synth.kicad.sch_gen.wired_layout import (
    GRID,
    ComponentInfo,
    NetRole,
    PinInfo,
    Placement,
    WiredLayoutEngine,
    outward_step,
    rotate_offset,
    snap,
)


def wires(schematic: Path) -> List[Tuple[float, float, float, float]]:
    """Read the wire segments from a schematic file.

    Args:
        schematic: Path to a .kicad_sch file.

    Returns:
        One ``(x1, y1, x2, y2)`` tuple per wire segment.
    """
    text = schematic.read_text(encoding="utf-8")
    return [
        tuple(float(value) for value in match)
        for match in re.findall(
            r"\(wire\s*\(pts\s*\(xy ([\d.-]+) ([\d.-]+)\)\s*\(xy ([\d.-]+) ([\d.-]+)\)",
            text,
        )
    ]


def junctions(schematic: Path) -> List[Tuple[float, float]]:
    """Read the junction points from a schematic file.

    Args:
        schematic: Path to a .kicad_sch file.

    Returns:
        One ``(x, y)`` tuple per junction.
    """
    text = schematic.read_text(encoding="utf-8")
    return [
        (float(x), float(y))
        for x, y in re.findall(r"\(junction\s*\(at ([\d.-]+) ([\d.-]+)\)", text)
    ]


def symbols(schematic: Path) -> List[Tuple[str, float, float, float]]:
    """Read the placed symbols from a schematic file.

    Args:
        schematic: Path to a .kicad_sch file.

    Returns:
        One ``(reference, x, y, rotation)`` tuple per placed symbol.
    """
    text = schematic.read_text(encoding="utf-8")
    found = re.findall(
        r'\(symbol\s*\(lib_id "[^"]+"\)\s*\(at ([\d.-]+) ([\d.-]+) ([\d.-]+)\)'
        r'(?:.*?)\(property "Reference" "([^"]+)"',
        text,
        re.S,
    )
    return [(ref, float(x), float(y), float(rot)) for x, y, rot, ref in found]


@pytest.fixture
def temp_dir():
    """Create a temporary directory for generated KiCad projects."""
    path = Path(tempfile.mkdtemp())
    yield path
    shutil.rmtree(path, ignore_errors=True)


class TestGeometryHelpers:
    """The coordinate maths the layout depends on."""

    def test_snap_rounds_onto_the_grid(self):
        """Coordinates land on KiCad's 50mil grid."""
        assert snap(0.0) == 0.0
        assert snap(1.0) == pytest.approx(GRID)
        assert snap(25.0) == pytest.approx(25.4)

    def test_unrotated_pin_offsets_flip_the_y_axis(self):
        """Symbol y grows upwards while schematic y grows downwards."""
        assert rotate_offset(0.0, 3.81, 0.0) == pytest.approx((0.0, -3.81))
        assert rotate_offset(0.0, -3.81, 0.0) == pytest.approx((0.0, 3.81))

    def test_quarter_turn_puts_pin_one_on_the_left(self):
        """At 90 degrees a two-pin part reads left to right.

        KiCad turns a placed symbol the opposite way round from the naive sign
        convention. Getting this wrong swaps a part end for end.
        """
        first, second = (
            rotate_offset(0.0, 3.81, 90.0),
            rotate_offset(0.0, -3.81, 90.0),
        )
        assert first[0] < second[0], "pin 1 should sit to the left of pin 2"
        assert first == pytest.approx((-3.81, 0.0))
        assert second == pytest.approx((3.81, 0.0))

    def test_three_quarter_turn_is_the_mirror(self):
        """At 270 degrees the same part reads right to left."""
        assert rotate_offset(0.0, 3.81, 270.0) == pytest.approx((3.81, 0.0))

    @pytest.mark.parametrize(
        "angle,expected",
        [(0, (2.54, 0.0)), (90, (0.0, -2.54)), (180, (-2.54, 0.0)), (270, (0.0, 2.54))],
    )
    def test_outward_step_follows_the_label_angle(self, angle, expected):
        """A label angle converts to the direction the text runs in."""
        assert outward_step(angle, 2.54) == pytest.approx(expected)


class TestEngineGrouping:
    """How the engine splits a sheet into groups."""

    @staticmethod
    def _passive(reference: str, first_net: str, second_net: str) -> ComponentInfo:
        return ComponentInfo(
            reference=reference,
            lib_id="Device:R",
            pins=[
                PinInfo(reference, "1", 0.0, 3.81, 270.0, first_net),
                PinInfo(reference, "2", 0.0, -3.81, 90.0, second_net),
            ],
            width=7.62,
            height=7.62,
        )

    def test_parts_sharing_a_signal_net_are_placed_together(self):
        """Two parts joined by a signal net end up on the same row."""
        engine = WiredLayoutEngine(
            components=[
                self._passive("R1", "IN", "MID"),
                self._passive("R2", "MID", "OUT"),
            ],
            net_roles={
                "IN": NetRole.SIGNAL,
                "MID": NetRole.SIGNAL,
                "OUT": NetRole.SIGNAL,
            },
            power_symbols={},
        )
        plan = engine.build()
        assert plan.placements["R1"].y == plan.placements["R2"].y
        assert plan.placements["R1"].x < plan.placements["R2"].x

    def test_unrelated_parts_are_placed_on_separate_rows(self):
        """Parts with no net in common do not sit side by side."""
        engine = WiredLayoutEngine(
            components=[
                self._passive("R1", "A", "B"),
                self._passive("R2", "C", "D"),
            ],
            net_roles={role: NetRole.SIGNAL for role in "ABCD"},
            power_symbols={},
        )
        plan = engine.build()
        assert plan.placements["R1"].y != plan.placements["R2"].y

    def test_series_parts_are_evenly_spaced(self):
        """A chain of parts uses one constant pitch."""
        engine = WiredLayoutEngine(
            components=[
                self._passive("R1", "N0", "N1"),
                self._passive("R2", "N1", "N2"),
                self._passive("R3", "N2", "N3"),
            ],
            net_roles={f"N{index}": NetRole.SIGNAL for index in range(4)},
            power_symbols={},
        )
        plan = engine.build()
        xs = sorted(placement.x for placement in plan.placements.values())
        gaps = [round(second - first, 3) for first, second in zip(xs, xs[1:])]
        assert len(set(gaps)) == 1, f"uneven spacing: {gaps}"

    def test_ground_becomes_a_power_symbol(self):
        """A pin on a power rail gets a symbol rather than a wire or a label."""
        engine = WiredLayoutEngine(
            components=[self._passive("C1", "SIG", "GND")],
            net_roles={"SIG": NetRole.SIGNAL, "GND": NetRole.POWER},
            power_symbols={"GND": "power:GND"},
        )
        plan = engine.build()
        assert [entry[1] for entry in plan.power_symbols] == ["GND"]
        assert ("C1", "2") in plan.wired_pins

    def test_a_net_reaching_off_sheet_is_left_to_labels(self):
        """A net the sheet cannot fully draw is not wired at all."""
        component = self._passive("R1", "IN", "OUT")
        # "OUT" also reaches a pin that is not on this sheet, modelled here by
        # a second pin record whose component is never placed.
        engine = WiredLayoutEngine(
            components=[component],
            net_roles={"IN": NetRole.SIGNAL, "OUT": NetRole.SIGNAL},
            power_symbols={},
        )
        engine._net_pins["OUT"].append(PinInfo("U9", "1", 0.0, 0.0, 0.0, "OUT"))
        plan = engine.build()
        assert "OUT" not in plan.fully_wired_nets


class TestGeneratedFilter:
    """The schematic produced for a resistor divider with a shunt capacitor."""

    @pytest.fixture
    def project(self, temp_dir):
        """Generate a two-resistor filter with a capacitor to ground."""

        @circuit(name="Filt")
        def filt(VIN: Input, VOUT: Output):
            gnd = Net("GND")
            first = Component(
                symbol="Device:R",
                ref="R",
                value="1k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            second = Component(
                symbol="Device:R",
                ref="R",
                value="2k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            shunt = Component(
                symbol="Device:C",
                ref="C",
                value="100nF",
                footprint="Capacitor_SMD:C_0603_1608Metric",
            )
            mid = Net("MID")
            first[1] += VIN
            first[2] += mid
            second[1] += mid
            second[2] += VOUT
            shunt[1] += mid
            shunt[2] += gnd

        @circuit(name="Board")
        def board():
            filt(Net("IN"), Net("OUT"))

        path = temp_dir / "filter_project"
        board().generate_kicad_project(
            str(path), force_regenerate=True, generate_pcb=False
        )
        return path / "Filt.kicad_sch"

    def test_series_parts_share_a_row(self, project):
        """The two resistors sit on one horizontal axis."""
        placed = {ref: (x, y, rot) for ref, x, y, rot in symbols(project)}
        assert placed["R1"][1] == placed["R2"][1]
        assert placed["R1"][2] == 90.0, "series parts are laid on their side"

    def test_the_shunt_hangs_below_the_node(self, project):
        """The capacitor sits under the point it decouples."""
        placed = {ref: (x, y, rot) for ref, x, y, rot in symbols(project)}
        assert placed["C1"][1] > placed["R1"][1], "the shunt drops below the axis"
        assert placed["C1"][2] == 0.0, "a shunt stands upright"

    def test_the_node_is_wired_not_labelled_at_every_pin(self, project):
        """The shared node is drawn as wires meeting at a junction."""
        assert wires(project), "the sheet should contain wire segments"
        points = junctions(project)
        assert len(points) == 1, f"expected one junction, got {points}"

        # Every wire is orthogonal.
        for x1, y1, x2, y2 in wires(project):
            assert x1 == x2 or y1 == y2, f"diagonal wire {(x1, y1, x2, y2)}"

    def test_the_junction_lies_between_the_resistors(self, project):
        """The node sits on the chain axis, between the two series parts."""
        placed = {ref: (x, y, rot) for ref, x, y, rot in symbols(project)}
        ((node_x, node_y),) = junctions(project)
        assert placed["R1"][0] < node_x < placed["R2"][0]
        assert node_y == placed["R1"][1]
        assert node_x == placed["C1"][0], "the shunt drops straight down"

    def test_ground_uses_a_power_symbol(self, project):
        """Ground never becomes a wire across the sheet or a label."""
        text = project.read_text(encoding="utf-8")
        assert '(lib_id "power:GND")' in text
        assert '(label "GND"' not in text
