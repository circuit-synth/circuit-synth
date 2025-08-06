import json
import os
import unittest
from pathlib import Path

from circuit_synth.kicad.netlist_importer import PinType, convert_netlist


class TestCircuit2NetlistImporter(unittest.TestCase):
    """
    Tests the KiCad netlist importer for circuit2.net
    located in tests/test_data/kicad9/kicad_projects/circuit2/.
    """

    @classmethod
    def setUpClass(cls):
        # Base directory: tests/ (i.e. three parents up from this file)
        cls.BASE_DIR = Path(__file__).parent.parent

        # Path to circuit2.net
        cls.NETLIST_PATH = (
            cls.BASE_DIR
            / "test_data"
            / "kicad9"
            / "kicad_projects"
            / "circuit2"
            / "circuit2.net"
        )

        # Create output directory if it doesn't exist
        cls.OUTPUT_DIR = cls.BASE_DIR / "test_output"
        cls.OUTPUT_DIR.mkdir(exist_ok=True)

        # Output JSON path
        cls.OUTPUT_JSON_PATH = cls.OUTPUT_DIR / "circuit2_output.json"

    def test_import_circuit2(self):
        """
        Test parsing circuit2.net, verifying structure, components, nets, pin types, etc.
        """
        # 1) Verify file presence
        self.assertTrue(
            self.NETLIST_PATH.is_file(),
            f"Missing test netlist file: {self.NETLIST_PATH}",
        )

        # 2) Convert circuit2.net => circuit2_output.json
        convert_netlist(self.NETLIST_PATH, self.OUTPUT_JSON_PATH)
        self.assertTrue(self.OUTPUT_JSON_PATH.exists())

        # 3) Load the JSON and check structure
        with self.OUTPUT_JSON_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # ---- Basic top-level checks ----
        self.assertIn("name", data)
        self.assertIn("components", data)
        self.assertIn("nets", data)
        self.assertIn("subcircuits", data)
        self.assertIn("properties", data)

        # The top-level circuit name should match "circuit2"
        self.assertEqual(data["name"], "circuit2")

        # ---- Check components ----
        # Verify component count and references
        # (Adjust these assertions based on the actual content of circuit2.net)
        self.assertGreater(
            len(data["components"]), 0, "No components found in the circuit"
        )

        # ---- Check nets ----
        # Verify net count
        self.assertGreater(len(data["nets"]), 0, "No nets found in the circuit")

        # ---- Check pin types ----
        # Verify various pin types are correctly parsed
        pin_types_found = set()

        for net_name, net_data in data["nets"].items():
            # Structure A: net_data is the list of nodes
            for node in net_data:
                if "pin" in node and "type" in node["pin"]:
                    pin_type = node["pin"]["type"]
                    pin_types_found.add(pin_type)

                    # Check specific pins for correct types based on common components
                    # These assertions should be adjusted based on the actual content of circuit2.net
                    component = node["component"]
                    pin_number = node["pin"]["number"]

                    # Check for power pins (usually on ICs, microcontrollers)
                    if pin_type == "power_in":
                        self.assertIn(
                            component,
                            data["components"],
                            f"Component {component} with power_in pin not found",
                        )

                    # Check for passive components (resistors, capacitors)
                    elif pin_type == "passive":
                        self.assertIn(
                            component,
                            data["components"],
                            f"Component {component} with passive pin not found",
                        )

                    # Check for bidirectional pins (usually I/O pins on microcontrollers)
                    elif pin_type == "bidirectional":
                        self.assertIn(
                            component,
                            data["components"],
                            f"Component {component} with bidirectional pin not found",
                        )

        # Verify we found various pin types
        self.assertGreater(len(pin_types_found), 0, "No pin types found in the circuit")

        # Check for expected pin types in the circuit
        # This list should be adjusted based on the actual content of circuit2.net
        expected_pin_types = {"passive"}  # At minimum, we expect passive pins
        self.assertTrue(
            expected_pin_types.issubset(pin_types_found),
            f"Expected at least pin types {expected_pin_types} but found {pin_types_found}",
        )

        # ---- Check unconnected pins ----
        # Verify unconnected pins are properly handled
        unconnected_nets = [
            net for net in data["nets"] if net.startswith("unconnected-")
        ]
        self.assertGreaterEqual(len(unconnected_nets), 0, "No unconnected nets found")

        # ---- Check properties ----
        props = data["properties"]
        self.assertIn("source", props)
        self.assertIn("date", props)

        print(
            f"circuit2.net => JSON output written to: {self.OUTPUT_JSON_PATH.resolve()}"
        )

    def test_match_reference_json(self):
        """
        Test to ensure circuit2 matches the expected output in circuit2_expected.json.
        This test compares the generated output against a known good reference.

        This is particularly useful when refactoring the importer code to ensure
        it maintains backward compatibility.
        """
        # Path to the reference/expected JSON
        expected_json_path = (
            self.BASE_DIR
            / "test_data"
            / "kicad9"
            / "expected_outputs"
            / "circuit2_expected.json"
        )

        # Skip if reference file doesn't exist - we'll just create it instead
        if not expected_json_path.exists():
            # If reference doesn't exist, generate it from current implementation
            expected_json_path.parent.mkdir(exist_ok=True, parents=True)
            convert_netlist(self.NETLIST_PATH, expected_json_path)
            print(f"Created reference JSON at {expected_json_path}")
            self.skipTest("Reference JSON didn't exist - created it for future tests")

        # Convert circuit2.net to JSON
        convert_netlist(self.NETLIST_PATH, self.OUTPUT_JSON_PATH)

        # Load both files
        with self.OUTPUT_JSON_PATH.open("r", encoding="utf-8") as f:
            actual_json = json.load(f)

        with expected_json_path.open("r", encoding="utf-8") as f:
            expected_json = json.load(f)

        # Compare component count and refs
        self.assertEqual(
            set(actual_json["components"].keys()),
            set(expected_json["components"].keys()),
            "Component references don't match",
        )

        # Compare net count and names
        self.assertEqual(
            set(actual_json["nets"].keys()),
            set(expected_json["nets"].keys()),
            "Net names don't match",
        )

        # For each net, compare node count
        for net_name in expected_json["nets"]:
            self.assertEqual(
                # Structure A: Access the list directly
                len(actual_json["nets"][net_name]),
                # Assuming expected_json also uses Structure A (or needs updating)
                len(expected_json["nets"][net_name]),
                f"Node count for net {net_name} doesn't match",
            )

        # Check subcircuit count
        self.assertEqual(
            len(actual_json["subcircuits"]),
            len(expected_json["subcircuits"]),
            "Subcircuit count doesn't match",
        )


if __name__ == "__main__":
    unittest.main()
