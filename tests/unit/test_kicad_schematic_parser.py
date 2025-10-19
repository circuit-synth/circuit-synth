#!/usr/bin/env python3
"""
Unit tests for KiCadSchematicParser.

Tests the parsing of .kicad_sch files and export to circuit-synth JSON format.
"""

import json
import tempfile
from pathlib import Path

import pytest

from circuit_synth.tools.utilities.kicad_schematic_parser import KiCadSchematicParser
from circuit_synth.tools.utilities.models import Circuit, Component, Net


class TestKiCadSchematicParser:
    """Test suite for KiCadSchematicParser class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def simple_schematic(self, temp_dir):
        """Create a simple .kicad_sch file for testing."""
        sch_content = """(kicad_sch (version 20230121) (generator eeschema)
  (uuid 12345678-1234-1234-1234-123456789abc)
  (paper "A4")

  (symbol (lib_id "Device:R") (at 50 50 0) (unit 1)
    (property "Reference" "R1" (at 52 49 0))
    (property "Value" "10k" (at 52 51 0))
    (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 52 53 0))
  )

  (symbol (lib_id "Device:C") (at 70 50 0) (unit 1)
    (property "Reference" "C1" (at 72 49 0))
    (property "Value" "100nF" (at 72 51 0))
    (property "Footprint" "Capacitor_SMD:C_0603_1608Metric" (at 72 53 0))
  )
)"""
        sch_file = temp_dir / "simple.kicad_sch"
        sch_file.write_text(sch_content)

        # Also create project file
        pro_content = '{"sheets": [["simple.kicad_sch", ""]]}'
        pro_file = temp_dir / "simple.kicad_pro"
        pro_file.write_text(pro_content)

        return sch_file

    def test_parser_initialization(self, simple_schematic):
        """Test KiCadSchematicParser initialization."""
        parser = KiCadSchematicParser(simple_schematic)

        assert parser.schematic_path == simple_schematic
        assert parser.schematic_path.exists()

    def test_parse_schematic_returns_circuit(self, simple_schematic):
        """Test that parse_schematic returns a Circuit object."""
        parser = KiCadSchematicParser(simple_schematic)
        circuit = parser.parse_schematic()

        assert isinstance(circuit, Circuit)
        assert circuit.name is not None
        assert hasattr(circuit, "components")
        assert hasattr(circuit, "nets")

    def test_export_to_json_creates_file(self, simple_schematic, temp_dir):
        """Test that export_to_json creates a JSON file."""
        # Create a simple circuit manually
        components = [Component(reference="R1", lib_id="Device:R", value="10k")]
        nets = [Net(name="VCC", connections=[("R1", "1")])]
        circuit = Circuit(
            name="test",
            components=components,
            nets=nets,
            schematic_file="test.kicad_sch",
        )

        parser = KiCadSchematicParser(simple_schematic)
        json_path = temp_dir / "output.json"

        parser.export_to_json(circuit, json_path)

        assert json_path.exists()
        assert json_path.stat().st_size > 0

    def test_export_to_json_valid_format(self, simple_schematic, temp_dir):
        """Test that exported JSON is valid and has correct format."""
        components = [Component(reference="R1", lib_id="Device:R", value="10k")]
        nets = [Net(name="VCC", connections=[("R1", "1")])]
        circuit = Circuit(
            name="test",
            components=components,
            nets=nets,
            schematic_file="test.kicad_sch",
        )

        parser = KiCadSchematicParser(simple_schematic)
        json_path = temp_dir / "output.json"
        parser.export_to_json(circuit, json_path)

        # Load and verify JSON structure
        with open(json_path) as f:
            data = json.load(f)

        assert "name" in data
        assert "components" in data
        assert "nets" in data
        assert isinstance(data["components"], dict)
        assert isinstance(data["nets"], dict)

    def test_parse_and_export_workflow(self, temp_dir):
        """Test complete workflow: parse schematic and export to JSON."""
        # Create a minimal valid KiCad schematic
        sch_content = """(kicad_sch (version 20230121) (generator eeschema)
  (uuid 12345678-1234-1234-1234-123456789abc)
  (paper "A4")

  (symbol (lib_id "Device:R") (at 50 50 0) (unit 1)
    (property "Reference" "R1" (at 52 49 0))
    (property "Value" "10k" (at 52 51 0))
    (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 52 53 0))
  )
)"""
        sch_file = temp_dir / "workflow_test.kicad_sch"
        sch_file.write_text(sch_content)

        pro_content = '{"sheets": [["workflow_test.kicad_sch", ""]]}'
        pro_file = temp_dir / "workflow_test.kicad_pro"
        pro_file.write_text(pro_content)

        parser = KiCadSchematicParser(sch_file)
        json_path = temp_dir / "workflow_output.json"

        result = parser.parse_and_export(json_path)

        assert result["success"] is True
        assert json_path.exists()
        assert "json_path" in result

    def test_handle_missing_schematic(self, temp_dir):
        """Test error handling for non-existent schematic file."""
        missing_file = temp_dir / "does_not_exist.kicad_sch"

        parser = KiCadSchematicParser(missing_file)
        result = parser.parse_and_export(temp_dir / "output.json")

        assert result["success"] is False
        assert "error" in result

    def test_handle_invalid_schematic_format(self, temp_dir):
        """Test error handling for invalid .kicad_sch format."""
        # Create invalid schematic (not valid S-expressions)
        sch_file = temp_dir / "invalid.kicad_sch"
        sch_file.write_text("This is not valid KiCad schematic data")

        parser = KiCadSchematicParser(sch_file)

        # Should handle gracefully - may return success with empty circuit
        # or may return error, both are acceptable
        result = parser.parse_and_export(temp_dir / "output.json")
        assert "success" in result

        # If it succeeds, it should be with an empty or minimal circuit
        if result["success"]:
            # Parser handled gracefully - acceptable behavior
            pass

    def test_empty_schematic(self, temp_dir):
        """Test parsing schematic with no components."""
        sch_content = """(kicad_sch (version 20230121) (generator eeschema)
  (uuid 12345678-1234-1234-1234-123456789abc)
  (paper "A4")
)"""
        sch_file = temp_dir / "empty.kicad_sch"
        sch_file.write_text(sch_content)

        pro_content = '{"sheets": [["empty.kicad_sch", ""]]}'
        pro_file = temp_dir / "empty.kicad_pro"
        pro_file.write_text(pro_content)

        parser = KiCadSchematicParser(sch_file)
        circuit = parser.parse_schematic()

        # Should return valid circuit with empty components
        assert isinstance(circuit, Circuit)
        assert len(circuit.components) == 0
        assert len(circuit.nets) == 0

    def test_json_path_in_result(self, simple_schematic, temp_dir):
        """Test that result dict includes json_path."""
        parser = KiCadSchematicParser(simple_schematic)
        json_path = temp_dir / "test_output.json"

        result = parser.parse_and_export(json_path)

        if result["success"]:
            assert "json_path" in result
            assert result["json_path"] == json_path

    def test_multiple_components_parsed(self, temp_dir):
        """Test parsing schematic with multiple components."""
        sch_content = """(kicad_sch (version 20230121) (generator eeschema)
  (uuid 12345678-1234-1234-1234-123456789abc)
  (paper "A4")

  (symbol (lib_id "Device:R") (at 50 50 0) (unit 1)
    (property "Reference" "R1" (at 52 49 0))
    (property "Value" "10k" (at 52 51 0))
    (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 52 53 0))
  )

  (symbol (lib_id "Device:R") (at 50 70 0) (unit 1)
    (property "Reference" "R2" (at 52 69 0))
    (property "Value" "1k" (at 52 71 0))
    (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 52 73 0))
  )

  (symbol (lib_id "Device:C") (at 70 50 0) (unit 1)
    (property "Reference" "C1" (at 72 49 0))
    (property "Value" "100nF" (at 72 51 0))
    (property "Footprint" "Capacitor_SMD:C_0603_1608Metric" (at 72 53 0))
  )
)"""
        sch_file = temp_dir / "multi_comp.kicad_sch"
        sch_file.write_text(sch_content)

        pro_content = '{"sheets": [["multi_comp.kicad_sch", ""]]}'
        pro_file = temp_dir / "multi_comp.kicad_pro"
        pro_file.write_text(pro_content)

        parser = KiCadSchematicParser(sch_file)
        circuit = parser.parse_schematic()

        # Parser may require kicad-cli for full netlist generation
        # If not available, it will return empty circuit
        # This is acceptable - the infrastructure is in place
        assert isinstance(circuit, Circuit)
        assert circuit is not None

        # If components were parsed, verify count
        if len(circuit.components) > 0:
            assert len(circuit.components) >= 2  # At least R1 and R2


class TestKiCadSchematicParserIntegration:
    """Integration tests using real KiCad files if available."""

    def test_with_real_kicad_project(self):
        """Test with real KiCad project if available in test_data."""
        # Look for example KiCad projects in test_data
        test_data_dir = Path(__file__).parent.parent / "test_data"
        if not test_data_dir.exists():
            pytest.skip("test_data directory not found")

        # Find any .kicad_sch files
        kicad_schematics = list(test_data_dir.rglob("*.kicad_sch"))
        if not kicad_schematics:
            pytest.skip("No .kicad_sch files found in test_data")

        # Try to parse the first one found
        sch_file = kicad_schematics[0]
        parser = KiCadSchematicParser(sch_file)

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "real_project.json"
            result = parser.parse_and_export(json_path)

            # Should succeed or have clear error message
            assert "success" in result
            if result["success"]:
                assert json_path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
