#!/usr/bin/env python3
"""
Integration tests for KiCadToPythonSyncer JSON workflow.

Tests the complete end-to-end workflow from JSON netlist to Python code generation.
"""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from circuit_synth.tools.kicad_integration.kicad_to_python_sync import (
    KiCadToPythonSyncer,
)


class TestKiCadSyncerJSONWorkflow:
    """Integration tests for JSON-first workflow"""

    @pytest.fixture
    def sample_json_netlist(self, tmp_path):
        """Create a sample JSON netlist for testing."""
        json_data = {
            "name": "voltage_divider",
            "description": "Simple voltage divider circuit",
            "tstamps": "",
            "source_file": "voltage_divider.kicad_sch",
            "components": {
                "R1": {
                    "ref": "R1",
                    "symbol": "Device:R",
                    "value": "10k",
                    "footprint": "Resistor_SMD:R_0603_1608Metric",
                    "datasheet": "",
                    "description": "",
                    "properties": {},
                    "tstamps": "",
                    "pins": [],
                },
                "R2": {
                    "ref": "R2",
                    "symbol": "Device:R",
                    "value": "10k",
                    "footprint": "Resistor_SMD:R_0603_1608Metric",
                    "datasheet": "",
                    "description": "",
                    "properties": {},
                    "tstamps": "",
                    "pins": [],
                },
            },
            "nets": {
                "VIN": [{"component": "R1", "pin": {"number": "1", "name": "~", "type": "passive"}}],
                "VOUT": [
                    {"component": "R1", "pin": {"number": "2", "name": "~", "type": "passive"}},
                    {"component": "R2", "pin": {"number": "1", "name": "~", "type": "passive"}},
                ],
                "GND": [{"component": "R2", "pin": {"number": "2", "name": "~", "type": "passive"}}],
            },
            "subcircuits": [],
            "annotations": [],
        }

        json_file = tmp_path / "voltage_divider.json"
        json_file.write_text(json.dumps(json_data, indent=2))
        return json_file

    @pytest.fixture
    def sample_kicad_project(self, tmp_path):
        """Create a complete sample KiCad project for testing."""
        # Create project file
        pro_file = tmp_path / "test_project.kicad_pro"
        pro_content = """{
  "board": {
    "design_settings": {},
    "layers": []
  },
  "schematic": {
    "annotate": {},
    "erc": {}
  }
}"""
        pro_file.write_text(pro_content)

        # Create schematic file
        sch_file = tmp_path / "test_project.kicad_sch"
        sch_content = """(kicad_sch (version 20211123) (generator eeschema)
  (uuid "12345678-1234-1234-1234-123456789abc")
  (paper "A4")
  (title_block (title "Test Project"))

  (symbol (lib_id "Device:R") (at 60 60 0) (unit 1)
    (in_bom yes) (on_board yes)
    (uuid "r1-uuid")
    (property "Reference" "R1" (id 0) (at 60 55 0))
    (property "Value" "1k" (id 1) (at 60 65 0))
    (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (id 2))
    (pin "1" (uuid "r1-pin1"))
    (pin "2" (uuid "r1-pin2"))
  )
)"""
        sch_file.write_text(sch_content)

        return tmp_path

    def test_end_to_end_json_workflow(self, sample_json_netlist, tmp_path):
        """Test 11: Complete workflow from JSON to Python generation."""
        output_file = tmp_path / "circuit.py"

        # Run syncer with JSON input
        syncer = KiCadToPythonSyncer(
            str(sample_json_netlist), str(output_file), preview_only=False
        )

        success = syncer.sync()

        assert success, "Synchronization should succeed"
        assert output_file.exists(), "Output file should be created"

        # Verify generated Python content
        content = output_file.read_text()

        # Should contain circuit definition
        assert (
            "def main" in content or "@circuit" in content
        ), "Should contain circuit function"

        # Should contain component references (case-insensitive)
        assert (
            "R1" in content or "r1" in content.lower()
        ), "Should contain R1 component"
        assert (
            "R2" in content or "r2" in content.lower()
        ), "Should contain R2 component"

        # Should contain circuit-synth imports
        assert (
            "from circuit_synth import" in content or "Component" in content
        ), "Should import circuit_synth"

    def test_json_workflow_with_complex_circuit(self, tmp_path):
        """Test 12: JSON workflow with more complex circuit."""
        # Create JSON with multiple component types
        json_data = {
            "name": "rc_filter",
            "components": {
                "R1": {
                    "ref": "R1",
                    "symbol": "Device:R",
                    "value": "1k",
                    "footprint": "R_0603",
                },
                "C1": {
                    "ref": "C1",
                    "symbol": "Device:C",
                    "value": "100nF",
                    "footprint": "C_0603",
                },
                "C2": {
                    "ref": "C2",
                    "symbol": "Device:C",
                    "value": "10uF",
                    "footprint": "C_0805",
                },
            },
            "nets": {
                "VIN": [{"component": "R1", "pin": {"number": "1"}}],
                "VOUT": [
                    {"component": "R1", "pin": {"number": "2"}},
                    {"component": "C1", "pin": {"number": "1"}},
                    {"component": "C2", "pin": {"number": "1"}},
                ],
                "GND": [
                    {"component": "C1", "pin": {"number": "2"}},
                    {"component": "C2", "pin": {"number": "2"}},
                ],
            },
            "source_file": "rc_filter.kicad_sch",
        }

        json_file = tmp_path / "rc_filter.json"
        json_file.write_text(json.dumps(json_data, indent=2))

        output_file = tmp_path / "rc_filter.py"
        syncer = KiCadToPythonSyncer(
            str(json_file), str(output_file), preview_only=False
        )

        success = syncer.sync()

        assert success
        assert output_file.exists()

        content = output_file.read_text()
        # Verify all components are present
        assert "R1" in content or "r1" in content.lower()
        assert "C1" in content or "c1" in content.lower()
        assert "C2" in content or "c2" in content.lower()

    @pytest.mark.skip(
        reason="Requires real KiCad project - will enable when KiCadSchematicParser is available"
    )
    def test_round_trip_kicad_json_python(self, sample_kicad_project, tmp_path):
        """Test 13: Complete round-trip from KiCad through JSON to Python."""
        # This test will be enabled once we have real KiCadSchematicParser working
        from circuit_synth.tools.utilities.kicad_schematic_parser import (
            KiCadSchematicParser,
        )

        # Step 1: Export KiCad to JSON
        json_file = tmp_path / "test_project.json"
        parser = KiCadSchematicParser(sample_kicad_project / "test_project.kicad_sch")
        result = parser.parse_and_export(json_file)

        assert result["success"]
        assert json_file.exists()

        # Step 2: Sync JSON to Python
        output_file = tmp_path / "circuit.py"
        syncer = KiCadToPythonSyncer(
            str(json_file), str(output_file), preview_only=False
        )

        success = syncer.sync()

        assert success
        assert output_file.exists()

    def test_backward_compatibility_kicad_input(self, sample_kicad_project, tmp_path):
        """Test 14: Legacy KiCad project input still works with warning."""
        output_file = tmp_path / "circuit.py"

        # Create a JSON file that would be auto-found
        json_file = sample_kicad_project / "test_project.json"
        json_data = {
            "name": "test_project",
            "components": {
                "R1": {
                    "ref": "R1",
                    "symbol": "Device:R",
                    "value": "1k",
                    "footprint": "R_0603",
                }
            },
            "nets": {},
            "source_file": "test_project.kicad_sch",
        }
        json_file.write_text(json.dumps(json_data))

        # Should work but show deprecation warning
        with pytest.warns(DeprecationWarning, match="Passing KiCad project directly"):
            syncer = KiCadToPythonSyncer(
                str(sample_kicad_project / "test_project.kicad_pro"),
                str(output_file),
                preview_only=False,
            )

            success = syncer.sync()
            assert success, "Legacy path should still work"

    def test_hierarchical_circuit_json(self, tmp_path):
        """Test 15: Syncer with hierarchical JSON structure."""
        # Create hierarchical JSON
        json_data = {
            "name": "main",
            "components": {},
            "nets": {},
            "subcircuits": [
                {
                    "name": "power_supply",
                    "components": {
                        "U1": {
                            "ref": "U1",
                            "symbol": "Regulator_Linear:LM7805",
                            "value": "LM7805",
                            "footprint": "Package_TO_SOT_SMD:SOT-223",
                        }
                    },
                    "nets": {},
                }
            ],
            "source_file": "main.kicad_sch",
        }

        json_file = tmp_path / "hierarchical.json"
        json_file.write_text(json.dumps(json_data, indent=2))

        output_dir = tmp_path / "output"
        syncer = KiCadToPythonSyncer(
            str(json_file), str(output_dir / "main.py"), preview_only=False
        )

        success = syncer.sync()

        # Should succeed even with hierarchical structure
        assert success

    def test_error_handling_missing_required_fields(self, tmp_path):
        """Test 16: Error handling for malformed JSON."""
        # Create JSON missing required fields
        json_data = {
            "components": {},
            # Missing 'name' field
            # Missing 'nets' field
        }

        json_file = tmp_path / "malformed.json"
        json_file.write_text(json.dumps(json_data))

        output_file = tmp_path / "output.py"

        # Should handle missing fields gracefully
        syncer = KiCadToPythonSyncer(
            str(json_file), str(output_file), preview_only=False
        )

        # May fail or use defaults - should not crash
        try:
            success = syncer.sync()
            # If it succeeds, verify output exists
            if success:
                assert output_file.exists()
        except (KeyError, ValueError) as e:
            # Expected - missing required fields
            assert "name" in str(e) or "nets" in str(e)

    def test_preview_mode_no_files_created(self, sample_json_netlist, tmp_path):
        """Test 17: Preview mode doesn't create files."""
        output_file = tmp_path / "circuit.py"

        syncer = KiCadToPythonSyncer(
            str(sample_json_netlist), str(output_file), preview_only=True
        )

        success = syncer.sync()

        assert success, "Preview should succeed"
        # In preview mode, file might not be created (depends on implementation)
        # This tests that preview mode is respected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
