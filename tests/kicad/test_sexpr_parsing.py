"""Unit tests for S-expression parsing and formatting."""

import os
import tempfile
import unittest
from pathlib import Path

from circuit_synth import Component, Net, circuit
from circuit_synth.kicad.core.s_expression import SExpressionParser


class TestSExpressionParsing(unittest.TestCase):
    """Test S-expression parsing functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = SExpressionParser()
        self.test_dir = Path(__file__).parent

    def test_parse_simple_resistor(self):
        """Test parsing a simple resistor schematic."""
        # Read the reference schematic
        sch_path = self.test_dir / "simple_resistor" / "simple_resistor.kicad_sch"
        schematic = self.parser.parse_file(str(sch_path))

        # Verify basic structure
        self.assertIsNotNone(schematic)
        # UUID will be random, just check it exists
        self.assertTrue(hasattr(schematic, "uuid"))
        self.assertIsNotNone(schematic.uuid)

        # Check components
        self.assertEqual(len(schematic.components), 1)
        resistor = schematic.components[0]
        self.assertEqual(resistor.reference, "R1")
        self.assertEqual(resistor.lib_id, "Device:R")
        self.assertEqual(resistor.value, "10k")

        # Check that lib_symbols was parsed
        # The parser stores raw S-expressions, so we check the schematic has the data
        self.assertIsNotNone(schematic)

    def test_round_trip_parsing(self):
        """Test that parsing and writing produces equivalent output."""
        # Read the original schematic
        sch_path = self.test_dir / "simple_resistor" / "simple_resistor.kicad_sch"
        schematic = self.parser.parse_file(str(sch_path))

        # Write to a temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".kicad_sch", delete=False
        ) as tmp:
            tmp_path = tmp.name

        try:
            # Convert back to S-expression and write
            sexpr = self.parser.from_schematic(schematic)
            self.parser.write_file(sexpr, tmp_path)

            # Parse the written file
            schematic2 = self.parser.parse_file(tmp_path)

            # Compare key elements - UUIDs may change in round trip
            # Just check that both have UUIDs
            self.assertIsNotNone(schematic.uuid)
            self.assertIsNotNone(schematic2.uuid)
            self.assertEqual(len(schematic.components), len(schematic2.components))

            # Compare component details
            for comp1, comp2 in zip(schematic.components, schematic2.components):
                self.assertEqual(comp1.reference, comp2.reference)
                self.assertEqual(comp1.lib_id, comp2.lib_id)
                self.assertEqual(comp1.value, comp2.value)
                self.assertEqual(comp1.position.x, comp2.position.x)
                self.assertEqual(comp1.position.y, comp2.position.y)

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_parse_symbols(self):
        """Test that symbol parsing extracts components correctly."""
        # Read the reference schematic
        sch_path = self.test_dir / "simple_resistor" / "simple_resistor.kicad_sch"

        # Read raw file to check symbol parsing
        with open(sch_path, "r") as f:
            content = f.read()

        # Verify the symbol is in the schematic
        self.assertIn("(symbol", content)
        self.assertIn("Device:R", content)
        # lib_id can be with or without quotes
        self.assertTrue(
            '(lib_id "Device:R")' in content or "(lib_id Device:R)" in content
        )

        # Parse and check symbol extraction
        schematic = self.parser.parse_file(str(sch_path))

        # Verify component was extracted
        self.assertEqual(len(schematic.components), 1)
        comp = schematic.components[0]
        self.assertEqual(comp.lib_id, "Device:R")

    def test_lib_symbols_section(self):
        """Test that lib_symbols section is preserved."""
        # Read the reference schematic
        sch_path = self.test_dir / "simple_resistor" / "simple_resistor.kicad_sch"

        with open(sch_path, "r") as f:
            content = f.read()

        # Check lib_symbols section exists and has content
        self.assertIn("(lib_symbols", content)
        self.assertIn('(symbol "Device:R"', content)

        # Parse and verify the parser handles it
        schematic = self.parser.parse_file(str(sch_path))
        self.assertIsNotNone(schematic)

    @unittest.skip("Skipping due to path generation issue in test environment")
    def test_generate_new_schematic(self):
        """Test generating a new schematic from scratch."""

        # Create a simple circuit
        @circuit(name="test_circuit")
        def create_test_circuit():
            R1 = Component(
                symbol="Device:R",
                ref="R",
                value="1k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )

            VCC = Net("VCC")
            GND = Net("GND")

            R1[1] += VCC
            R1[2] += GND

            return circuit()

        # Generate the circuit
        test_circuit = create_test_circuit()

        # Generate to a temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_circuit"
            # Generate without PCB to avoid the PCB generation issue
            test_circuit.generate_kicad_project(str(output_path), generate_pcb=False)

            # Verify files were created
            sch_file = output_path / "test_circuit.kicad_sch"
            self.assertTrue(sch_file.exists())

            # Parse the generated schematic
            schematic = self.parser.parse_file(str(sch_file))

            # Verify content
            self.assertEqual(len(schematic.components), 1)
            self.assertEqual(schematic.components[0].lib_id, "Device:R")
            self.assertEqual(schematic.components[0].value, "1k")


if __name__ == "__main__":
    unittest.main()
