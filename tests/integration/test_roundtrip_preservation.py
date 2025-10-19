"""
Integration tests for round-trip schematic preservation.

Tests that manual KiCad edits (component positions, wires, labels) are preserved
when re-generating projects with force_regenerate=False.
"""

import tempfile
from pathlib import Path

import pytest

import kicad_sch_api as ksa
from circuit_synth import Component, Net, circuit
from kicad_sch_api.core.types import Point


class TestRoundTripPreservation:
    """Test round-trip update preservation functionality."""

    def test_component_position_preservation(self):
        """Test that component positions are preserved across updates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test_position"
            output_dir.mkdir()

            # Step 1: Generate initial circuit
            @circuit(name="test_position")
            def simple_circuit():
                r1 = Component(
                    "Device:R",
                    ref="R1",
                    value="10k",
                    footprint="Resistor_SMD:R_0603_1608Metric",
                )
                r2 = Component(
                    "Device:R",
                    ref="R2",
                    value="10k",
                    footprint="Resistor_SMD:R_0603_1608Metric",
                )
                vcc = Net("VCC")
                gnd = Net("GND")
                mid = Net("MID")
                r1[1] += vcc
                r1[2] += mid
                r2[1] += mid
                r2[2] += gnd
                return r1, r2

            c = simple_circuit()
            c.generate_kicad_project(
                str(output_dir), force_regenerate=True, generate_pcb=False
            )

            # Find schematic file
            sch_path = None
            for path in [
                output_dir / "test_position.kicad_sch",
                Path(tmpdir) / "test_position.kicad_sch",
            ]:
                if path.exists():
                    sch_path = path
                    break

            assert sch_path is not None, "Schematic file not created"
            assert sch_path.exists(), f"Schematic not found at {sch_path}"

            # Step 2: Modify component position with kicad-sch-api
            sch = ksa.Schematic.load(str(sch_path))
            r1 = sch.components.get("R1")
            assert r1 is not None, "R1 not found in schematic"

            original_pos = r1.position
            new_pos = Point(180.0, 120.0)
            r1.position = new_pos
            sch.save(str(sch_path), preserve_format=True)

            # Step 3: Re-generate with force_regenerate=False (update mode)
            c2 = simple_circuit()
            c2.generate_kicad_project(
                str(output_dir), force_regenerate=False, generate_pcb=False
            )

            # Step 4: Verify position was preserved
            sch_after = ksa.Schematic.load(str(sch_path))
            r1_after = sch_after.components.get("R1")
            assert r1_after is not None, "R1 not found after update"

            # Check position preserved (with small tolerance for floating point)
            assert abs(r1_after.position.x - new_pos.x) < 0.01, (
                f"R1 X position not preserved: "
                f"expected {new_pos.x}, got {r1_after.position.x}"
            )
            assert abs(r1_after.position.y - new_pos.y) < 0.01, (
                f"R1 Y position not preserved: "
                f"expected {new_pos.y}, got {r1_after.position.y}"
            )

    def test_value_update_with_position_preservation(self):
        """Test that component values update while positions are preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test_value_update"
            output_dir.mkdir()

            # Step 1: Generate initial circuit
            @circuit(name="test_value_update")
            def circuit_v1():
                r1 = Component(
                    "Device:R",
                    ref="R1",
                    value="10k",
                    footprint="Resistor_SMD:R_0603_1608Metric",
                )
                vcc = Net("VCC")
                gnd = Net("GND")
                r1[1] += vcc
                r1[2] += gnd
                return r1

            c = circuit_v1()
            c.generate_kicad_project(
                str(output_dir), force_regenerate=True, generate_pcb=False
            )

            # Find schematic
            sch_path = None
            for path in [
                output_dir / "test_value_update.kicad_sch",
                Path(tmpdir) / "test_value_update.kicad_sch",
            ]:
                if path.exists():
                    sch_path = path
                    break

            assert sch_path is not None, "Schematic file not created"

            # Step 2: Move component
            sch = ksa.Schematic.load(str(sch_path))
            r1 = sch.components.get("R1")
            assert r1 is not None, "R1 not found"

            new_pos = Point(150.0, 100.0)
            r1.position = new_pos
            sch.save(str(sch_path), preserve_format=True)

            # Step 3: Update circuit with new value
            @circuit(name="test_value_update")
            def circuit_v2():
                r1 = Component(
                    "Device:R",
                    ref="R1",
                    value="22k",  # Changed value
                    footprint="Resistor_SMD:R_0603_1608Metric",
                )
                vcc = Net("VCC")
                gnd = Net("GND")
                r1[1] += vcc
                r1[2] += gnd
                return r1

            c2 = circuit_v2()
            c2.generate_kicad_project(
                str(output_dir), force_regenerate=False, generate_pcb=False
            )

            # Step 4: Verify both position preserved AND value updated
            sch_after = ksa.Schematic.load(str(sch_path))
            r1_after = sch_after.components.get("R1")
            assert r1_after is not None, "R1 not found after update"

            # Check position preserved
            assert abs(r1_after.position.x - new_pos.x) < 0.01, (
                f"Position not preserved: "
                f"expected {new_pos.x}, got {r1_after.position.x}"
            )
            assert abs(r1_after.position.y - new_pos.y) < 0.01, (
                f"Position not preserved: "
                f"expected {new_pos.y}, got {r1_after.position.y}"
            )

            # Check value updated
            assert (
                r1_after.value == "22k"
            ), f"Value not updated: expected '22k', got '{r1_after.value}'"

    def test_wire_preservation(self):
        """Test that manually added wires are preserved across updates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test_wires"
            output_dir.mkdir()

            # Step 1: Generate initial circuit
            @circuit(name="test_wires")
            def simple_circuit():
                r1 = Component(
                    "Device:R",
                    ref="R1",
                    value="10k",
                    footprint="Resistor_SMD:R_0603_1608Metric",
                )
                vcc = Net("VCC")
                gnd = Net("GND")
                r1[1] += vcc
                r1[2] += gnd
                return r1

            c = simple_circuit()
            c.generate_kicad_project(
                str(output_dir), force_regenerate=True, generate_pcb=False
            )

            # Find schematic
            sch_path = None
            for path in [
                output_dir / "test_wires.kicad_sch",
                Path(tmpdir) / "test_wires.kicad_sch",
            ]:
                if path.exists():
                    sch_path = path
                    break

            assert sch_path is not None, "Schematic file not created"

            # Step 2: Add manual wire
            sch = ksa.Schematic.load(str(sch_path))
            wire_start = Point(50.0, 50.0)
            wire_end = Point(100.0, 50.0)
            wire_uuid = sch.add_wire(start=wire_start, end=wire_end)
            sch.save(str(sch_path), preserve_format=True)

            # Step 3: Re-generate
            c2 = simple_circuit()
            c2.generate_kicad_project(
                str(output_dir), force_regenerate=False, generate_pcb=False
            )

            # Step 4: Verify wire preserved
            sch_after = ksa.Schematic.load(str(sch_path))
            wire_found = False
            for wire in sch_after.wires:
                if wire.uuid == wire_uuid:
                    wire_found = True
                    break

            assert wire_found, f"Manual wire with UUID {wire_uuid} was not preserved"

    def test_label_preservation(self):
        """Test that manually added labels are preserved across updates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test_labels"
            output_dir.mkdir()

            # Step 1: Generate initial circuit
            @circuit(name="test_labels")
            def simple_circuit():
                r1 = Component(
                    "Device:R",
                    ref="R1",
                    value="10k",
                    footprint="Resistor_SMD:R_0603_1608Metric",
                )
                vcc = Net("VCC")
                gnd = Net("GND")
                r1[1] += vcc
                r1[2] += gnd
                return r1

            c = simple_circuit()
            c.generate_kicad_project(
                str(output_dir), force_regenerate=True, generate_pcb=False
            )

            # Find schematic
            sch_path = None
            for path in [
                output_dir / "test_labels.kicad_sch",
                Path(tmpdir) / "test_labels.kicad_sch",
            ]:
                if path.exists():
                    sch_path = path
                    break

            assert sch_path is not None, "Schematic file not created"

            # Step 2: Add manual label
            sch = ksa.Schematic.load(str(sch_path))
            label_pos = Point(75.0, 60.0)
            label_uuid = sch.add_label("MANUAL_SIGNAL", position=label_pos)
            sch.save(str(sch_path), preserve_format=True)

            # Step 3: Re-generate
            c2 = simple_circuit()
            c2.generate_kicad_project(
                str(output_dir), force_regenerate=False, generate_pcb=False
            )

            # Step 4: Verify label preserved
            sch_after = ksa.Schematic.load(str(sch_path))
            label_found = False
            for label in sch_after._data.get("labels", []):
                if label.get("uuid") == label_uuid:
                    label_found = True
                    assert (
                        label.get("text") == "MANUAL_SIGNAL"
                    ), "Label text not preserved"
                    break

            assert (
                label_found
            ), f"Manual label with UUID {label_uuid} was not preserved"
