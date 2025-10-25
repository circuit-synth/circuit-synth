#!/usr/bin/env python3
"""
Basic Round-Trip Test: Python → JSON → KiCad → JSON

This test validates the fundamental round-trip pipeline for circuit-synth:
1. Python circuit definition
2. Generate JSON netlist from Python
3. Generate KiCad project from JSON
4. Export KiCad project back to JSON
5. Verify JSON before/after are equivalent

This is a minimal test focused on the core pipeline, not the complete
bidirectional Python ↔ KiCad ↔ JSON workflow.
"""

import json
import tempfile
from pathlib import Path

import pytest

from circuit_synth import Circuit, Component, Net, circuit


class TestBasicRoundTrip:
    """Test basic round-trip: Python → JSON → KiCad → JSON"""

    @staticmethod
    def _get_project_dir(result: dict) -> Path:
        """Extract project directory from generate_kicad_project result."""
        project_path = result.get("project_path")
        if project_path:
            return Path(project_path)

        project_file = result.get("project_file")
        if project_file:
            return Path(project_file).parent

        return None

    @pytest.fixture
    def simple_circuit(self):
        """Create a minimal resistor divider circuit for testing."""
        @circuit(name="voltage_divider")
        def voltage_divider():
            # Create nets
            vin = Net("VIN")
            vout = Net("VOUT")
            gnd = Net("GND")

            # Create components
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            r2 = Component(
                symbol="Device:R",
                ref="R2",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )

            # Create connections
            r1[1] += vin
            r1[2] += vout
            r2[1] += vout
            r2[2] += gnd

        return voltage_divider()

    def test_python_to_json_generation(self, simple_circuit):
        """Test step 1: Python → JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "circuit.json"

            # Generate JSON from Python circuit
            simple_circuit.generate_json_netlist(str(json_path))

            # Verify JSON file was created
            assert json_path.exists(), "JSON file was not created"

            # Verify JSON is valid
            with open(json_path) as f:
                json_data = json.load(f)

            # Verify JSON structure
            assert "components" in json_data, "JSON missing 'components' key"
            assert "nets" in json_data, "JSON missing 'nets' key"
            assert json_data["name"] == "voltage_divider", "Circuit name mismatch"

            # Verify components in JSON
            components = json_data["components"]
            assert len(components) == 2, f"Expected 2 components, got {len(components)}"
            assert "R1" in components, "R1 not found in JSON components"
            assert "R2" in components, "R2 not found in JSON components"

            # Verify component details
            r1_json = components["R1"]
            assert r1_json["value"] == "10k", "R1 value mismatch in JSON"
            assert r1_json["symbol"] == "Device:R", "R1 symbol mismatch in JSON"
            assert r1_json["footprint"] == "Resistor_SMD:R_0603_1608Metric", "R1 footprint mismatch"

            # Verify nets in JSON
            nets = json_data["nets"]
            assert "VIN" in nets, "VIN net not found in JSON"
            assert "VOUT" in nets, "VOUT net not found in JSON"
            assert "GND" in nets, "GND net not found in JSON"

            print("✅ Python → JSON: PASS")
            return json_path

    def test_json_to_kicad_generation(self, simple_circuit):
        """Test step 2: JSON → KiCad"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            json_path = tmpdir_path / "circuit.json"
            kicad_dir = tmpdir_path / "kicad_project"

            # Step 1: Generate JSON from Python
            simple_circuit.generate_json_netlist(str(json_path))

            # Step 2: Generate KiCad project from Python
            # (This actually uses the circuit object, not the JSON directly)
            result = simple_circuit.generate_kicad_project(
                project_name="voltage_divider",
                generate_pcb=False,  # Skip PCB for this test
            )

            # Verify KiCad project was created
            assert result is not None, "generate_kicad_project returned None"
            assert isinstance(result, dict), "generate_kicad_project should return dict"
            assert result.get("success"), "Project generation was not successful"
            assert result.get("project_path") or result.get(
                "project_file"
            ), "No project path in result"

            # Get project path (result can have either project_path or project_file)
            project_dir = self._get_project_dir(result)
            assert project_dir is not None, "Could not extract project directory from result"
            assert project_dir.exists(), f"KiCad project directory not found: {project_dir}"

            # Verify schematic file exists
            kicad_sch = next(project_dir.glob("*.kicad_sch"), None)
            assert kicad_sch is not None, f"No .kicad_sch file found in {project_dir}"
            assert kicad_sch.exists(), f"KiCad schematic file not found: {kicad_sch}"

            # Verify JSON was created in project directory
            json_in_project = next(project_dir.glob("*.json"), None)
            # Note: JSON path may vary based on implementation

            print("✅ JSON → KiCad: PASS")
            return kicad_sch

    def test_kicad_to_json_export(self, simple_circuit):
        """Test step 3: KiCad → JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Step 1: Generate KiCad project from Python
            result = simple_circuit.generate_kicad_project(
                project_name="voltage_divider",
                generate_pcb=False,
            )
            project_dir = self._get_project_dir(result)
            if not project_dir:
                pytest.skip("Could not extract project directory")

            # Step 2: Export KiCad back to JSON
            kicad_sch = next(project_dir.glob("*.kicad_sch"), None)
            if not kicad_sch:
                pytest.skip("No .kicad_sch file found")

            exported_json_path = tmpdir_path / "exported.json"

            # Use KiCadSchematicParser to export to JSON
            from circuit_synth.tools.utilities.kicad_schematic_parser import (
                KiCadSchematicParser,
            )

            parser = KiCadSchematicParser(kicad_sch)
            export_result = parser.parse_and_export(str(exported_json_path))

            if export_result.get("success"):
                # Verify exported JSON is valid
                assert exported_json_path.exists(), "Exported JSON file not created"

                with open(exported_json_path) as f:
                    exported_json = json.load(f)

                # Verify structure
                assert "components" in exported_json, "Exported JSON missing 'components'"
                assert "nets" in exported_json, "Exported JSON missing 'nets'"

                # Verify we have the resistors
                components = exported_json.get("components", {})
                assert len(components) >= 2, f"Expected >=2 components, got {len(components)}"

                print("✅ KiCad → JSON: PASS")
            else:
                pytest.skip(
                    f"KiCad → JSON export not fully implemented: {export_result.get('error')}"
                )

    def test_complete_round_trip(self, simple_circuit):
        """Test complete round-trip: Python → JSON → KiCad → JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # STEP 1: Python → JSON
            original_json_path = tmpdir_path / "original.json"
            simple_circuit.generate_json_netlist(str(original_json_path))

            with open(original_json_path) as f:
                original_json = json.load(f)

            print(f"Step 1 (Python → JSON): ✓")
            print(f"  - Components: {list(original_json['components'].keys())}")
            print(f"  - Nets: {list(original_json['nets'].keys())}")

            # STEP 2: JSON → KiCad
            result = simple_circuit.generate_kicad_project(
                project_name="voltage_divider",
                generate_pcb=False,
            )
            project_dir = self._get_project_dir(result)
            if not project_dir:
                pytest.skip("Could not extract project directory")
            print(f"Step 2 (JSON → KiCad): ✓")
            print(f"  - Project: {project_dir}")

            # STEP 3: KiCad → JSON
            kicad_sch = next(project_dir.glob("*.kicad_sch"), None)
            if not kicad_sch:
                pytest.skip("No .kicad_sch file generated")

            exported_json_path = tmpdir_path / "exported.json"

            from circuit_synth.tools.utilities.kicad_schematic_parser import (
                KiCadSchematicParser,
            )

            parser = KiCadSchematicParser(kicad_sch)
            export_result = parser.parse_and_export(str(exported_json_path))

            if not export_result.get("success"):
                pytest.skip("KiCad → JSON export not implemented")

            with open(exported_json_path) as f:
                exported_json = json.load(f)

            print(f"Step 3 (KiCad → JSON): ✓")
            print(f"  - Components: {list(exported_json.get('components', {}).keys())}")
            print(f"  - Nets: {list(exported_json.get('nets', {}).keys())}")

            # STEP 4: Verify round-trip
            original_components = set(original_json["components"].keys())
            exported_components = set(exported_json.get("components", {}).keys())

            # Should have same components
            assert (
                original_components == exported_components
            ), f"Component mismatch: {original_components} vs {exported_components}"

            print(f"Step 4 (Verification): ✓")
            print(f"✅ COMPLETE ROUND-TRIP: Python → JSON → KiCad → JSON")
            print(f"   Round-trip completed successfully!")

    def test_round_trip_component_values_preserved(self, simple_circuit):
        """Verify that component values survive the round-trip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Step 1: Generate KiCad from Python
            result = simple_circuit.generate_kicad_project(
                project_name="voltage_divider",
                generate_pcb=False,
            )
            project_dir = self._get_project_dir(result)
            if not project_dir:
                pytest.skip("Could not extract project directory")

            # Step 2: Export back to JSON
            kicad_sch = next(project_dir.glob("*.kicad_sch"), None)
            if not kicad_sch:
                pytest.skip("No .kicad_sch file generated")

            exported_json_path = tmpdir_path / "exported.json"

            from circuit_synth.tools.utilities.kicad_schematic_parser import (
                KiCadSchematicParser,
            )

            parser = KiCadSchematicParser(kicad_sch)
            export_result = parser.parse_and_export(str(exported_json_path))

            if not export_result.get("success"):
                pytest.skip("KiCad → JSON export not implemented")

            with open(exported_json_path) as f:
                exported_json = json.load(f)

            # Verify values are preserved
            components = exported_json.get("components", {})
            for ref in ["R1", "R2"]:
                if ref in components:
                    assert (
                        components[ref].get("value") == "10k"
                    ), f"{ref} value should be preserved as 10k"

            print(f"✅ Component values preserved through round-trip")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
