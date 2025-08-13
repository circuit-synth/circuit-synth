"""
Tests for S-Expression Manipulator Layer.
"""

import pytest

from circuit_synth.kicad.sexpr_manipulator import SExpressionManipulator


class TestSExpressionManipulator:
    """Test SExpressionManipulator class."""

    def test_parse_blank_schematic(self):
        """Test parsing a blank schematic."""
        blank_content = '(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0") (paper "A4") (lib_symbols) (symbol_instances))'

        manipulator = SExpressionManipulator(blank_content)

        # Check that it parsed without error
        assert manipulator._data is not None
        assert isinstance(manipulator._data, list)

        # Convert back to string
        result = manipulator.to_string()
        assert "kicad_sch" in result
        assert "version" in result
        assert "A4" in result

    def test_create_blank_schematic(self):
        """Test creating a blank schematic from scratch."""
        manipulator = SExpressionManipulator()
        manipulator.create_blank_schematic()

        result = manipulator.to_string()

        # Check required sections exist
        assert "kicad_sch" in result
        assert "version" in result
        assert "generator" in result
        assert "paper" in result
        assert "lib_symbols" in result
        assert "symbol_instances" in result

    def test_find_section(self):
        """Test finding sections in S-expression."""
        manipulator = SExpressionManipulator()
        manipulator.create_blank_schematic()

        # Find existing section
        lib_symbols = manipulator.find_section("lib_symbols")
        assert lib_symbols is not None
        assert len(lib_symbols) >= 1
        assert str(lib_symbols[0]) == "lib_symbols"

        # Try to find non-existent section
        missing = manipulator.find_section("nonexistent")
        assert missing is None

    def test_add_remove_section(self):
        """Test adding and removing sections."""
        manipulator = SExpressionManipulator()
        manipulator.create_blank_schematic()

        # Add new section
        content = ["item1", "item2"]
        section = manipulator.add_section("test_section", content)
        assert section is not None
        assert str(section[0]) == "test_section"
        assert section[1] == "item1"
        assert section[2] == "item2"

        # Verify it can be found
        found = manipulator.find_section("test_section")
        assert found == section

        # Remove section
        removed = manipulator.remove_section("test_section")
        assert removed is True

        # Verify it's gone
        found = manipulator.find_section("test_section")
        assert found is None

        # Try to remove non-existent section
        removed = manipulator.remove_section("nonexistent")
        assert removed is False

    def test_add_symbol(self):
        """Test adding a symbol."""
        manipulator = SExpressionManipulator()
        manipulator.create_blank_schematic()

        symbol_data = {
            "lib_id": "Device:R",
            "reference": "R1",
            "value": "10k",
            "position": (100, 50),
            "footprint": "Resistor_SMD:R_0603_1608Metric",
            "uuid": "test-uuid-1234",
        }

        symbol = manipulator.add_symbol(symbol_data)

        # Verify symbol structure
        assert symbol is not None
        assert str(symbol[0]) == "symbol"

        # Check that symbol appears in output
        result = manipulator.to_string()
        assert "Device:R" in result
        assert "R1" in result
        assert "10k" in result
        assert "test-uuid-1234" in result

    def test_find_symbol(self):
        """Test finding symbols by reference."""
        manipulator = SExpressionManipulator()
        manipulator.create_blank_schematic()

        # Add a symbol
        symbol_data = {
            "lib_id": "Device:R",
            "reference": "R1",
            "value": "10k",
            "position": (100, 50),
        }
        manipulator.add_symbol(symbol_data)

        # Find the symbol
        found = manipulator.find_symbol("R1")
        assert found is not None
        assert str(found[0]) == "symbol"

        # Try to find non-existent symbol
        missing = manipulator.find_symbol("R999")
        assert missing is None

    def test_remove_symbol(self):
        """Test removing symbols by reference."""
        manipulator = SExpressionManipulator()
        manipulator.create_blank_schematic()

        # Add symbols
        manipulator.add_symbol(
            {"lib_id": "Device:R", "reference": "R1", "value": "10k"}
        )
        manipulator.add_symbol(
            {"lib_id": "Device:R", "reference": "R2", "value": "22k"}
        )

        # Verify both exist
        assert manipulator.find_symbol("R1") is not None
        assert manipulator.find_symbol("R2") is not None

        # Remove R1
        removed = manipulator.remove_symbol("R1")
        assert removed is True

        # Verify R1 is gone, R2 remains
        assert manipulator.find_symbol("R1") is None
        assert manipulator.find_symbol("R2") is not None

        # Try to remove non-existent symbol
        removed = manipulator.remove_symbol("R999")
        assert removed is False

    def test_roundtrip_consistency(self):
        """Test that parse -> modify -> serialize maintains consistency."""
        # Start with reference blank schematic
        original = '(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0") (paper "A4") (lib_symbols) (symbol_instances))'

        manipulator = SExpressionManipulator(original)

        # Add a component
        manipulator.add_symbol(
            {
                "lib_id": "Device:R",
                "reference": "R1",
                "value": "10k",
                "position": (121.92, 68.58),
            }
        )

        # Serialize back
        result = manipulator.to_string()

        # Parse again to verify structure
        manipulator2 = SExpressionManipulator(result)
        found = manipulator2.find_symbol("R1")
        assert found is not None

        # Verify no corruption
        assert "kicad_sch" in result
        assert "Device:R" in result
        assert "R1" in result

    def test_pretty_formatting(self):
        """Test that pretty formatting produces readable output."""
        manipulator = SExpressionManipulator()
        manipulator.create_blank_schematic()

        result = manipulator.to_string(pretty=True)

        # Check indentation exists (tabs)
        assert "\t" in result

        # Check that it's properly structured
        lines = result.split("\n")
        assert len(lines) > 5  # Should be multi-line

        # First line should be opening
        assert lines[0].strip().startswith("(kicad_sch")

    def test_symbol_with_minimal_data(self):
        """Test creating symbol with minimal required data."""
        manipulator = SExpressionManipulator()
        manipulator.create_blank_schematic()

        # Only lib_id is truly required
        symbol_data = {"lib_id": "Device:C"}

        symbol = manipulator.add_symbol(symbol_data)
        assert symbol is not None

        result = manipulator.to_string()
        assert "Device:C" in result
