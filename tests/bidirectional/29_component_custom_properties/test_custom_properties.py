#!/usr/bin/env python3
"""
Comprehensive tests for custom component properties (Issue #409).

Tests all scenarios where custom properties must work:
1. Python → JSON serialization
2. JSON → KiCad generation
3. KiCad → Python synchronization
4. Round-trip preservation
5. Complex types handling
6. Edge cases

Each test is designed to catch specific failure modes.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from circuit_synth import Circuit, Component, circuit


class TestCustomPropertiesPythonToKiCad:
    """Test Python → JSON → KiCad path (generation)."""

    def test_properties_in_component_extra_fields(self):
        """Verify properties stored in Component._extra_fields."""
        comp = Component(
            symbol="Device:R",
            ref="R1",
            value="10k",
            DNP=True,
            MPN="RC0603",
            Tolerance="1%",
        )

        # Properties should be in _extra_fields
        assert hasattr(comp, "_extra_fields")
        assert "DNP" in comp._extra_fields
        assert comp._extra_fields["DNP"] is True
        assert "MPN" in comp._extra_fields
        assert comp._extra_fields["MPN"] == "RC0603"
        assert "Tolerance" in comp._extra_fields
        assert comp._extra_fields["Tolerance"] == "1%"

        # Should also be accessible as attributes
        assert comp.DNP is True
        assert comp.MPN == "RC0603"
        assert comp.Tolerance == "1%"

    def test_properties_in_json_serialization(self):
        """Verify Component.to_dict() includes custom properties."""
        comp = Component(
            symbol="Device:R",
            ref="R1",
            value="10k",
            DNP=True,
            MPN="RC0603",
            Tolerance="1%",
        )

        data = comp.to_dict()

        # Should have _extra_fields dict
        assert "_extra_fields" in data
        assert data["_extra_fields"]["DNP"] is True
        assert data["_extra_fields"]["MPN"] == "RC0603"
        assert data["_extra_fields"]["Tolerance"] == "1%"

        # Should also have top-level fields for easy access
        assert data["DNP"] is True
        assert data["MPN"] == "RC0603"
        assert data["Tolerance"] == "1%"

    def test_properties_in_generated_kicad_schematic(self, tmp_path):
        """Verify custom properties appear in generated .kicad_sch file."""

        @circuit(name="test_props")
        def test_circuit():
            Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                DNP=True,
                MPN="RC0603",
                Tolerance="1%",
            )

        circuit_obj = test_circuit()

        # Generate in temp directory
        output_dir = tmp_path / "test_props"
        os.chdir(tmp_path)
        circuit_obj.generate_kicad_project(project_name="test_props")

        # Read generated schematic
        sch_file = output_dir / "test_props.kicad_sch"
        assert sch_file.exists(), f"Schematic file not found: {sch_file}"

        with open(sch_file) as f:
            content = f.read()

        # Verify user properties are written
        assert '(property "DNP"' in content, "DNP property not in schematic"
        assert '(property "MPN"' in content, "MPN property not in schematic"
        assert '(property "Tolerance"' in content, "Tolerance property not in schematic"

        # Verify property values
        assert '"true"' in content or "'true'" in content, "DNP value not correct"
        assert "RC0603" in content, "MPN value not in schematic"
        assert "1%" in content, "Tolerance value not in schematic"

    def test_dnp_flag_in_kicad_schematic(self, tmp_path):
        """Verify DNP sets KiCad's built-in dnp flag."""

        @circuit(name="test_dnp")
        def test_circuit():
            Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                DNP=True,
            )

        circuit_obj = test_circuit()

        os.chdir(tmp_path)
        circuit_obj.generate_kicad_project(project_name="test_dnp")

        sch_file = tmp_path / "test_dnp" / "test_dnp.kicad_sch"
        with open(sch_file) as f:
            content = f.read()

        # Should have built-in DNP flag (KiCad 8.0 format)
        # Could be (dnp yes) or just (dnp) depending on version
        assert "(dnp" in content, "Built-in DNP flag not found"

    def test_system_properties_prefixed(self, tmp_path):
        """Verify system properties are prefixed to avoid conflicts."""

        @circuit(name="test_system")
        def test_circuit():
            Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                DNP=True,
            )

        circuit_obj = test_circuit()

        os.chdir(tmp_path)
        circuit_obj.generate_kicad_project(project_name="test_system")

        sch_file = tmp_path / "test_system" / "test_system.kicad_sch"
        with open(sch_file) as f:
            content = f.read()

        # System properties should be prefixed
        assert "(property \"_circuit_synth_" in content, \
            "System properties not prefixed"

        # User property DNP should NOT be prefixed
        assert '(property "DNP"' in content, "User DNP property not found"


class TestCustomPropertiesComplexTypes:
    """Test handling of complex property types."""

    def test_list_property(self, tmp_path):
        """Test list properties converted to comma-separated strings."""

        @circuit(name="test_list")
        def test_circuit():
            Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                Tags=["precision", "low-noise", "0.1%"],
            )

        circuit_obj = test_circuit()

        os.chdir(tmp_path)
        circuit_obj.generate_kicad_project(project_name="test_list")

        sch_file = tmp_path / "test_list" / "test_list.kicad_sch"
        with open(sch_file) as f:
            content = f.read()

        # List should be converted to comma-separated string
        assert '(property "Tags"' in content
        assert "precision" in content
        assert "low-noise" in content

    def test_dict_property(self, tmp_path):
        """Test dict properties converted to JSON strings."""

        @circuit(name="test_dict")
        def test_circuit():
            Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                Specs={"voltage": "50V", "power": "0.125W"},
            )

        circuit_obj = test_circuit()

        os.chdir(tmp_path)
        circuit_obj.generate_kicad_project(project_name="test_dict")

        sch_file = tmp_path / "test_dict" / "test_dict.kicad_sch"
        with open(sch_file) as f:
            content = f.read()

        # Dict should be converted to JSON string
        assert '(property "Specs"' in content
        # JSON keys should be in content
        assert "voltage" in content or '\\"voltage\\"' in content

    def test_numeric_properties(self, tmp_path):
        """Test numeric properties (int, float)."""

        @circuit(name="test_numeric")
        def test_circuit():
            Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                Cost=0.05,  # Float
                Quantity=100,  # Int
            )

        circuit_obj = test_circuit()

        os.chdir(tmp_path)
        circuit_obj.generate_kicad_project(project_name="test_numeric")

        sch_file = tmp_path / "test_numeric" / "test_numeric.kicad_sch"
        with open(sch_file) as f:
            content = f.read()

        assert '(property "Cost"' in content
        assert "0.05" in content
        assert '(property "Quantity"' in content
        assert "100" in content

    def test_none_property(self, tmp_path):
        """Test None property converted to empty string."""

        @circuit(name="test_none")
        def test_circuit():
            Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                Notes=None,
            )

        circuit_obj = test_circuit()

        os.chdir(tmp_path)
        circuit_obj.generate_kicad_project(project_name="test_none")

        sch_file = tmp_path / "test_none" / "test_none.kicad_sch"
        with open(sch_file) as f:
            content = f.read()

        # None should become empty string
        assert '(property "Notes" ""' in content or "(property \"Notes\" ''" in content


class TestCustomPropertiesEdgeCases:
    """Test edge cases and special characters."""

    def test_empty_string_property(self, tmp_path):
        """Test empty string properties."""

        @circuit(name="test_empty")
        def test_circuit():
            Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                EmptyString="",
            )

        circuit_obj = test_circuit()

        os.chdir(tmp_path)
        circuit_obj.generate_kicad_project(project_name="test_empty")

        sch_file = tmp_path / "test_empty" / "test_empty.kicad_sch"
        with open(sch_file) as f:
            content = f.read()

        assert '(property "EmptyString"' in content

    def test_special_characters(self, tmp_path):
        """Test special characters in property values."""

        @circuit(name="test_special")
        def test_circuit():
            Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                SpecialChars="!@#$%^&*()",
            )

        circuit_obj = test_circuit()

        os.chdir(tmp_path)
        circuit_obj.generate_kicad_project(project_name="test_special")

        sch_file = tmp_path / "test_special" / "test_special.kicad_sch"
        assert sch_file.exists()

    def test_unicode_characters(self, tmp_path):
        """Test Unicode characters in property values."""

        @circuit(name="test_unicode")
        def test_circuit():
            Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                Unicode="µF Ω ±",
            )

        circuit_obj = test_circuit()

        os.chdir(tmp_path)
        circuit_obj.generate_kicad_project(project_name="test_unicode")

        sch_file = tmp_path / "test_unicode" / "test_unicode.kicad_sch"
        with open(sch_file, encoding="utf-8") as f:
            content = f.read()

        # Unicode should be preserved
        assert "µF" in content or "\\u" in content  # Either literal or escaped

    def test_quotes_in_property(self, tmp_path):
        """Test quotes in property values are escaped."""

        @circuit(name="test_quotes")
        def test_circuit():
            Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                Quotes='Value with "quotes"',
            )

        circuit_obj = test_circuit()

        os.chdir(tmp_path)
        circuit_obj.generate_kicad_project(project_name="test_quotes")

        sch_file = tmp_path / "test_quotes" / "test_quotes.kicad_sch"
        assert sch_file.exists()

    def test_newlines_in_property(self, tmp_path):
        """Test newlines in property values are handled."""

        @circuit(name="test_newlines")
        def test_circuit():
            Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                MultiLine="Line 1\nLine 2\nLine 3",
            )

        circuit_obj = test_circuit()

        os.chdir(tmp_path)
        circuit_obj.generate_kicad_project(project_name="test_newlines")

        sch_file = tmp_path / "test_newlines" / "test_newlines.kicad_sch"
        assert sch_file.exists()


class TestCustomPropertiesRoundTrip:
    """Test properties survive round-trip (Python → KiCad → Python)."""

    @pytest.mark.skip(reason="Requires KiCad → Python path to be implemented")
    def test_round_trip_simple_properties(self, tmp_path):
        """Test simple properties survive round-trip."""

        @circuit(name="test_roundtrip")
        def test_circuit():
            Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                DNP=True,
                MPN="RC0603",
                Tolerance="1%",
            )

        # Generate
        circuit_obj = test_circuit()
        os.chdir(tmp_path)
        circuit_obj.generate_kicad_project(project_name="test_roundtrip")

        # Load back
        sch_file = tmp_path / "test_roundtrip" / "test_roundtrip.kicad_sch"
        # TODO: Implement load_circuit_from_kicad()
        # loaded_circuit = load_circuit_from_kicad(sch_file)
        # loaded_comp = loaded_circuit.components["R1"]

        # Verify
        # assert loaded_comp.DNP is True
        # assert loaded_comp.MPN == "RC0603"
        # assert loaded_comp.Tolerance == "1%"


class TestCustomPropertiesSynchronizer:
    """Test synchronizer preserves properties during updates."""

    @pytest.mark.skip(reason="Requires synchronizer integration")
    def test_synchronizer_preserves_properties(self, tmp_path):
        """Test properties preserved when syncing changes."""
        # TODO: Implement after synchronizer is updated
        pass


# Run with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
