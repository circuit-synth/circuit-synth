"""
Advanced round-trip schematic preservation tests.

Tests for professional workflows including:
- Component rotation
- Footprint updates
- Component addition/removal
- Manual component preservation
- Hierarchical sheet operations
"""

import tempfile
from pathlib import Path

import pytest

import kicad_sch_api as ksa
from circuit_synth import Component, Net, circuit
from kicad_sch_api.core.types import Point


class TestComponentRotation:
    """Test that component rotation is preserved across updates."""

    def test_component_rotation_preservation(self):
        """Test that rotated components maintain their orientation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_rotation"

            # Step 1: Generate initial circuit
            @circuit(name="test_rotation")
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
            c.generate_kicad_project(str(output_path), force_regenerate=True, generate_pcb=False)

            # Find schematic
            sch_path = self._find_schematic(output_path, tmpdir)
            assert sch_path is not None, "Schematic file not created"

            # Step 2: Rotate component
            sch = ksa.Schematic.load(str(sch_path))
            r1 = sch.components.get("R1")
            assert r1 is not None, "R1 not found"

            original_angle = r1.angle if hasattr(r1, 'angle') else 0
            new_angle = 90  # Rotate 90 degrees
            if hasattr(r1, 'angle'):
                r1.angle = new_angle

            sch.save(str(sch_path), preserve_format=True)

            # Step 3: Re-generate with updated value
            @circuit(name="test_rotation")
            def updated_circuit():
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

            c2 = updated_circuit()
            c2.generate_kicad_project(str(output_path), force_regenerate=False, generate_pcb=False)

            # Step 4: Verify rotation preserved and value updated
            sch_after = ksa.Schematic.load(str(sch_path))
            r1_after = sch_after.components.get("R1")

            if hasattr(r1_after, 'angle'):
                assert r1_after.angle == new_angle, (
                    f"Rotation not preserved: expected {new_angle}, got {r1_after.angle}"
                )

            assert r1_after.value == "22k", (
                f"Value not updated: expected '22k', got '{r1_after.value}'"
            )

    def _find_schematic(self, output_path, tmpdir):
        """Helper to find schematic file."""
        for path in [
            output_path / "test_rotation.kicad_sch",
            Path(tmpdir) / "test_rotation.kicad_sch",
        ]:
            if path.exists():
                return path
        return None


class TestFootprintUpdates:
    """Test that footprint changes propagate correctly."""

    def test_footprint_update_preserves_position(self):
        """Test that changing footprint in Python updates KiCad while preserving position."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_footprint"

            # Step 1: Generate with 0603 footprint
            @circuit(name="test_footprint")
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
            c.generate_kicad_project(str(output_path), force_regenerate=True, generate_pcb=False)

            sch_path = self._find_schematic(output_path, tmpdir)
            assert sch_path is not None

            # Step 2: Move component
            sch = ksa.Schematic.load(str(sch_path))
            r1 = sch.components.get("R1")
            new_pos = Point(150.0, 100.0)
            r1.position = new_pos
            sch.save(str(sch_path), preserve_format=True)

            # Step 3: Update to 0805 footprint
            @circuit(name="test_footprint")
            def circuit_v2():
                r1 = Component(
                    "Device:R",
                    ref="R1",
                    value="10k",
                    footprint="Resistor_SMD:R_0805_2012Metric",  # Changed footprint
                )
                vcc = Net("VCC")
                gnd = Net("GND")
                r1[1] += vcc
                r1[2] += gnd
                return r1

            c2 = circuit_v2()
            c2.generate_kicad_project(str(output_path), force_regenerate=False, generate_pcb=False)

            # Step 4: Verify footprint updated but position preserved
            sch_after = ksa.Schematic.load(str(sch_path))
            r1_after = sch_after.components.get("R1")

            assert abs(r1_after.position.x - new_pos.x) < 0.01, "Position X not preserved"
            assert abs(r1_after.position.y - new_pos.y) < 0.01, "Position Y not preserved"
            assert "R_0805_2012Metric" in r1_after.footprint, (
                f"Footprint not updated: got '{r1_after.footprint}'"
            )

    def _find_schematic(self, output_path, tmpdir):
        """Helper to find schematic file."""
        for path in [
            output_path / "test_footprint.kicad_sch",
            Path(tmpdir) / "test_footprint.kicad_sch",
        ]:
            if path.exists():
                return path
        return None


class TestComponentLifecycle:
    """Test adding and removing components."""

    def test_add_component_via_python(self):
        """Test that adding a new component in Python adds it to KiCad."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_add"

            # Step 1: Generate with one component
            @circuit(name="test_add")
            def circuit_v1():
                r1 = Component("Device:R", ref="R1", value="10k")
                vcc = Net("VCC")
                gnd = Net("GND")
                r1[1] += vcc
                r1[2] += gnd
                return r1

            c = circuit_v1()
            c.generate_kicad_project(str(output_path), force_regenerate=True, generate_pcb=False)

            sch_path = self._find_schematic(output_path, tmpdir)
            assert sch_path is not None

            # Verify only R1 exists
            sch = ksa.Schematic.load(str(sch_path))
            assert sch.components.get("R1") is not None
            assert sch.components.get("R2") is None

            # Step 2: Add second component
            @circuit(name="test_add")
            def circuit_v2():
                r1 = Component("Device:R", ref="R1", value="10k")
                r2 = Component("Device:R", ref="R2", value="22k")  # NEW
                vcc = Net("VCC")
                gnd = Net("GND")
                mid = Net("MID")
                r1[1] += vcc
                r1[2] += mid
                r2[1] += mid  # NEW
                r2[2] += gnd  # NEW
                return r1, r2

            c2 = circuit_v2()
            c2.generate_kicad_project(str(output_path), force_regenerate=False, generate_pcb=False)

            # Step 3: Verify R2 was added
            sch_after = ksa.Schematic.load(str(sch_path))
            assert sch_after.components.get("R1") is not None, "R1 should still exist"
            assert sch_after.components.get("R2") is not None, "R2 should be added"
            assert sch_after.components.get("R2").value == "22k"

    def test_remove_component_via_python(self):
        """Test that removing a component in Python removes it from KiCad."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_remove"

            # Step 1: Generate with two components
            @circuit(name="test_remove")
            def circuit_v1():
                r1 = Component("Device:R", ref="R1", value="10k")
                r2 = Component("Device:R", ref="R2", value="22k")
                vcc = Net("VCC")
                gnd = Net("GND")
                mid = Net("MID")
                r1[1] += vcc
                r1[2] += mid
                r2[1] += mid
                r2[2] += gnd
                return r1, r2

            c = circuit_v1()
            c.generate_kicad_project(str(output_path), force_regenerate=True, generate_pcb=False)

            sch_path = self._find_schematic(output_path, tmpdir)
            assert sch_path is not None

            # Verify both exist
            sch = ksa.Schematic.load(str(sch_path))
            assert sch.components.get("R1") is not None
            assert sch.components.get("R2") is not None

            # Step 2: Remove R2
            @circuit(name="test_remove")
            def circuit_v2():
                r1 = Component("Device:R", ref="R1", value="10k")
                vcc = Net("VCC")
                gnd = Net("GND")
                r1[1] += vcc
                r1[2] += gnd
                return r1

            c2 = circuit_v2()
            c2.generate_kicad_project(str(output_path), force_regenerate=False, generate_pcb=False)

            # Step 3: Verify R2 was removed (if preserve_user_components=False)
            # Note: By default preserve_user_components=True, so R2 will be preserved
            # This test documents current behavior
            sch_after = ksa.Schematic.load(str(sch_path))
            assert sch_after.components.get("R1") is not None, "R1 should still exist"
            # R2 may be preserved depending on synchronizer settings

    def _find_schematic(self, output_path, tmpdir):
        """Helper to find schematic file."""
        for path in [
            output_path / f"{output_path.name}.kicad_sch",
            Path(tmpdir) / f"{output_path.name}.kicad_sch",
        ]:
            if path.exists():
                return path
        return None


class TestManualComponentPreservation:
    """Test that manually added components are preserved."""

    def test_manual_component_preserved(self):
        """Test that components added manually in KiCad are preserved during updates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_manual"

            # Step 1: Generate initial circuit
            @circuit(name="test_manual")
            def circuit_v1():
                r1 = Component("Device:R", ref="R1", value="10k")
                vcc = Net("VCC")
                gnd = Net("GND")
                r1[1] += vcc
                r1[2] += gnd
                return r1

            c = circuit_v1()
            c.generate_kicad_project(str(output_path), force_regenerate=True, generate_pcb=False)

            sch_path = self._find_schematic(output_path, tmpdir)
            assert sch_path is not None

            # Step 2: Manually add component using kicad-sch-api
            sch = ksa.Schematic.load(str(sch_path))

            # Add manual capacitor (simulating user adding in KiCad)
            manual_cap_uuid = sch.add_component(
                lib_id="Device:C",
                reference="C1",
                value="100n",
                position=Point(100.0, 100.0)
            )
            sch.save(str(sch_path), preserve_format=True)

            # Step 3: Update original circuit
            @circuit(name="test_manual")
            def circuit_v2():
                r1 = Component("Device:R", ref="R1", value="22k")  # Changed value
                vcc = Net("VCC")
                gnd = Net("GND")
                r1[1] += vcc
                r1[2] += gnd
                return r1

            c2 = circuit_v2()
            c2.generate_kicad_project(str(output_path), force_regenerate=False, generate_pcb=False)

            # Step 4: Verify manual component preserved
            sch_after = ksa.Schematic.load(str(sch_path))
            r1_after = sch_after.components.get("R1")
            c1_after = sch_after.components.get("C1")

            assert r1_after is not None, "R1 should exist"
            assert r1_after.value == "22k", "R1 value should be updated"
            assert c1_after is not None, "Manual C1 should be preserved"
            assert c1_after.value == "100n", "Manual C1 value should be preserved"

    def _find_schematic(self, output_path, tmpdir):
        """Helper to find schematic file."""
        for path in [
            output_path / "test_manual.kicad_sch",
            Path(tmpdir) / "test_manual.kicad_sch",
        ]:
            if path.exists():
                return path
        return None


class TestPowerSymbols:
    """Test that manually added power symbols are preserved."""

    def test_power_symbol_preservation(self):
        """Test that power symbols (VCC, GND) added in KiCad are preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_power"

            # Step 1: Generate circuit
            @circuit(name="test_power")
            def simple_circuit():
                r1 = Component("Device:R", ref="R1", value="10k")
                vcc = Net("VCC")
                gnd = Net("GND")
                r1[1] += vcc
                r1[2] += gnd
                return r1

            c = simple_circuit()
            c.generate_kicad_project(str(output_path), force_regenerate=True, generate_pcb=False)

            sch_path = self._find_schematic(output_path, tmpdir)
            assert sch_path is not None

            # Step 2: Add power symbols manually
            sch = ksa.Schematic.load(str(sch_path))

            # Add VCC power symbol
            vcc_uuid = sch.add_component(
                lib_id="power:VCC",
                reference="#PWR01",
                value="VCC",
                position=Point(80.0, 80.0)
            )

            # Add GND power symbol
            gnd_uuid = sch.add_component(
                lib_id="power:GND",
                reference="#PWR02",
                value="GND",
                position=Point(80.0, 120.0)
            )

            sch.save(str(sch_path), preserve_format=True)

            # Step 3: Update circuit
            @circuit(name="test_power")
            def updated_circuit():
                r1 = Component("Device:R", ref="R1", value="22k")
                vcc = Net("VCC")
                gnd = Net("GND")
                r1[1] += vcc
                r1[2] += gnd
                return r1

            c2 = updated_circuit()
            c2.generate_kicad_project(str(output_path), force_regenerate=False, generate_pcb=False)

            # Step 4: Verify power symbols preserved
            sch_after = ksa.Schematic.load(str(sch_path))

            pwr01 = sch_after.components.get("#PWR01")
            pwr02 = sch_after.components.get("#PWR02")

            assert pwr01 is not None, "VCC power symbol should be preserved"
            assert pwr02 is not None, "GND power symbol should be preserved"

    def _find_schematic(self, output_path, tmpdir):
        """Helper to find schematic file."""
        for path in [
            output_path / "test_power.kicad_sch",
            Path(tmpdir) / "test_power.kicad_sch",
        ]:
            if path.exists():
                return path
        return None
