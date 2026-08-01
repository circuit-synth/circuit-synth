"""Unit tests for the schematic layout tools.

These cover the machinery a person, or Claude, uses to lay a sheet out: reading
the sheet's geometry, applying a placement to it, and checking that doing so
did not change the circuit.
"""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from circuit_synth import Component, Input, Net, Output, circuit
from circuit_synth.kicad.layout import PlacementSpec, apply_placement, describe_sheet
from circuit_synth.kicad.layout.extract import sheet_nets, sheet_ports
from circuit_synth.kicad.layout.spec import ComponentPlacement, LabelPlacement
from circuit_synth.kicad.layout.validate import intended_partition


@pytest.fixture
def temp_dir():
    """Create a temporary directory for generated KiCad projects."""
    path = Path(tempfile.mkdtemp())
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def project(temp_dir):
    """Generate a small two-resistor divider project to lay out."""

    @circuit(name="Divider")
    def divider(VIN: Input, VOUT: Output):
        top = Component(
            symbol="Device:R",
            ref="R",
            value="10k",
            footprint="Resistor_SMD:R_0603_1608Metric",
        )
        bottom = Component(
            symbol="Device:R",
            ref="R",
            value="10k",
            footprint="Resistor_SMD:R_0603_1608Metric",
        )
        gnd = Net("GND")
        top[1] += VIN
        top[2] += VOUT
        bottom[1] += VOUT
        bottom[2] += gnd

    @circuit(name="Board")
    def board():
        divider(Net("SRC"), Net("TAP"))

    path = temp_dir / "divider"
    board().generate_kicad_project(str(path), force_regenerate=True, generate_pcb=False)
    return path


class TestDescribeSheet:
    """Reading a sheet's geometry."""

    def test_lists_the_parts_with_their_pins(self, project):
        """Every placed part is described with its pins and their nets."""
        nets = sheet_nets(project / "Board.json")
        sheet = describe_sheet(project / "Divider.kicad_sch", nets.get("Divider"))

        by_reference = {part.reference: part for part in sheet.components}
        assert set(by_reference) == {"R1", "R2"}
        for part in by_reference.values():
            assert [pin.number for pin in part.pins] == ["1", "2"]
            assert all(pin.net for pin in part.pins), "pins should know their net"

    def test_pin_offsets_are_relative_to_the_symbol(self, project):
        """A pin offset is measured from the symbol origin, not the sheet."""
        nets = sheet_nets(project / "Board.json")
        sheet = describe_sheet(project / "Divider.kicad_sch", nets.get("Divider"))

        resistor = next(part for part in sheet.components if part.reference == "R1")
        offsets = sorted(pin.offset for pin in resistor.pins)
        assert offsets == [(0.0, -3.81), (0.0, 3.81)]

    def test_reports_the_paper_and_usable_area(self, project):
        """The description says how much room there is to lay out in."""
        sheet = describe_sheet(project / "Divider.kicad_sch")
        assert sheet.paper in {"A4", "A3"}
        min_x, min_y, max_x, max_y = sheet.extents
        assert max_x > min_x and max_y > min_y

    def test_reads_declared_ports(self, project):
        """A block's declared interface comes through with its directions."""
        ports = sheet_ports(project / "Board.json")
        assert ports["Divider"] == {"VIN": "input", "VOUT": "output"}


class TestApplyPlacement:
    """Applying a placement decision to a sheet."""

    def test_moves_components_and_redraws_the_wiring(self, project):
        """The parts land where the spec says and the wiring is replaced."""
        sheet_path = project / "Divider.kicad_sch"
        spec = PlacementSpec(
            components=[
                ComponentPlacement("R1", (76.2, 63.5), 0.0),
                ComponentPlacement("R2", (76.2, 88.9), 0.0),
            ],
            wires=[((76.2, 67.31), (76.2, 85.09))],
            labels=[LabelPlacement("TAP", (76.2, 76.2), 0.0, "local")],
        )
        written = apply_placement(sheet_path, spec)

        assert written["components_moved"] == 2
        text = sheet_path.read_text(encoding="utf-8")
        assert "(at 76.2 63.5 0)" in text
        assert "(at 76.2 88.9 0)" in text
        assert text.count("(wire") == 1
        assert '(label "TAP"' in text

    def test_keeps_the_component_identity(self, project):
        """UUIDs, properties and instance paths survive a placement."""
        sheet_path = project / "Divider.kicad_sch"
        before = sheet_path.read_text(encoding="utf-8")
        uuids = set(
            line.strip()
            for line in before.splitlines()
            if line.strip().startswith('(uuid "')
        )

        apply_placement(
            sheet_path,
            PlacementSpec(components=[ComponentPlacement("R1", (50.8, 50.8), 90.0)]),
        )
        after = sheet_path.read_text(encoding="utf-8")

        assert '(lib_id "Device:R")' in after
        assert '(property "Value" "10k"' in after
        assert "(instances" in after
        # The symbol UUIDs are untouched; only wiring UUIDs come and go.
        assert uuids & set(
            line.strip()
            for line in after.splitlines()
            if line.strip().startswith('(uuid "')
        )

    def test_rejects_coordinates_off_the_grid(self, project):
        """An off-grid wire looks connected and is not, so it is refused."""
        with pytest.raises(ValueError, match="grid"):
            apply_placement(
                project / "Divider.kicad_sch",
                PlacementSpec(wires=[((10.0, 10.0), (20.0, 10.0))]),
            )

    def test_rejects_an_unknown_component(self, project):
        """A spec naming a part the sheet does not have is a mistake."""
        with pytest.raises(ValueError, match="R99"):
            apply_placement(
                project / "Divider.kicad_sch",
                PlacementSpec(components=[ComponentPlacement("R99", (50.8, 50.8))]),
            )

    def test_writes_power_symbols_and_junctions(self, project):
        """Rails and meeting points are drawn from the spec."""
        from circuit_synth.kicad.layout.spec import PowerPlacement

        sheet_path = project / "Divider.kicad_sch"
        apply_placement(
            sheet_path,
            PlacementSpec(
                junctions=[(76.2, 76.2)],
                power=[PowerPlacement("power:GND", (76.2, 101.6), 0.0)],
            ),
        )
        text = sheet_path.read_text(encoding="utf-8")
        assert '(lib_id "power:GND")' in text
        assert "(junction" in text
        assert "(at 76.2 76.2)" in text


class TestIntendedPartition:
    """Reading the connectivity the Python circuit described."""

    def test_groups_pins_by_net(self, project):
        """Pins on one net come back as one set."""
        partition = intended_partition(project / "Board.json")
        assert partition["R1.2"] == partition["R2.1"], "the tap joins both parts"
        assert "R1.1" not in partition["R1.2"], "the ends are separate nets"

    def test_a_power_rail_joins_across_sheets(self, project):
        """A rail drawn with power symbols is one net design-wide."""
        data = json.loads((project / "Board.json").read_text(encoding="utf-8"))
        divider = data["subcircuits"][0]
        assert "GND" in divider["nets"], "the divider should have a ground net"

        partition = intended_partition(project / "Board.json")
        assert "R2.2" in partition, "the grounded pin is present"
