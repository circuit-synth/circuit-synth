import unittest
import json
import os
from pathlib import Path

from circuit_synth.kicad.netlist_importer import convert_netlist, PinType


class TestCircuit1NetlistImporter(unittest.TestCase):
    """
    Tests the KiCad netlist importer for circuit1.net 
    located in tests/test_data/kicad9/kicad_projects/circuit1/.
    """

    @classmethod
    def setUpClass(cls):
        # Base directory: tests/ (i.e. three parents up from this file)
        cls.BASE_DIR = Path(__file__).parent.parent

        # Path to circuit1.net
        cls.NETLIST_PATH = cls.BASE_DIR / "test_data" / "kicad9" / "kicad_projects" / "circuit1" / "circuit1.net"
        
        # Create output directory if it doesn't exist
        cls.OUTPUT_DIR = cls.BASE_DIR / "test_output"
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        
        # Output JSON path
        cls.OUTPUT_JSON_PATH = cls.OUTPUT_DIR / "circuit1_output.json"

    def test_import_circuit1(self):
        """
        Test parsing circuit1.net, verifying structure, components, nets, etc.
        This test ensures that:
        1. The file exists
        2. The netlist can be converted to JSON
        3. The JSON has the correct structure
        4. Components are properly parsed with their properties
        5. Nets are properly parsed with their nodes
        6. Properties are correctly extracted
        """
        # 1) Verify file presence
        self.assertTrue(
            self.NETLIST_PATH.is_file(),
            f"Missing test netlist file: {self.NETLIST_PATH}"
        )

        # 2) Convert circuit1.net => circuit1_output.json
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

        # The top-level circuit name should match "circuit1"
        self.assertEqual(data["name"], "circuit1")

        # ---- Check components ----
        # Verify component count and references
        expected_components = set(data["components"].keys())
        self.assertGreater(len(expected_components), 0, "No components found in the circuit")
        
        # Check specific component values if they exist
        for component_ref, component_data in data["components"].items():
            self.assertIn("value", component_data, f"Component {component_ref} missing 'value' property")
            if "footprint" in component_data:
                self.assertIsInstance(component_data["footprint"], str,
                                     f"Component {component_ref} has invalid footprint")
        
        # ---- Check nets ----
        # Verify net count and structure
        nets = data["nets"]
        self.assertGreater(len(nets), 0, "No nets found in the circuit")
        
        # Check that each net has the required fields
        for net_name, net_data in nets.items():
            # Structure A: net_data is the list of nodes
            self.assertIsInstance(net_data, list, f"Net {net_name} data should be a list (Structure A)")
            
            # Check that each node has the required fields
            # Structure A: net_data is the list of nodes
            for node in net_data:
                self.assertIn("component", node, f"Node in net {net_name} missing 'component' field")
                self.assertIn("pin", node, f"Node in net {net_name} missing 'pin' field")
                self.assertIn("number", node["pin"], f"Pin in net {net_name} missing 'number' field")
        
        # ---- Check properties ----
        props = data["properties"]
        self.assertIn("source", props)
        self.assertIn("date", props)
        
        print(f"circuit1.net => JSON output written to: {self.OUTPUT_JSON_PATH.resolve()}")

    def test_match_reference_json(self):
        """
        Test to ensure circuit1 matches the expected output in circuit1_expected.json.
        This test compares the generated output against a known good reference.
        
        This is particularly useful when refactoring the importer code to ensure
        it maintains backward compatibility.
        """
        # Path to the reference/expected JSON
        expected_json_path = self.BASE_DIR / "test_data" / "kicad9" / "expected_outputs" / "circuit1_expected.json"
        
        # Skip if reference file doesn't exist - we'll just create it instead
        if not expected_json_path.exists():
            # If reference doesn't exist, generate it from current implementation
            expected_json_path.parent.mkdir(exist_ok=True, parents=True)
            convert_netlist(self.NETLIST_PATH, expected_json_path)
            print(f"Created reference JSON at {expected_json_path}")
            self.skipTest("Reference JSON didn't exist - created it for future tests")
        
        # Convert circuit1.net to JSON
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
            "Component references don't match"
        )
        
        # Compare net count and names
        self.assertEqual(
            set(actual_json["nets"].keys()),
            set(expected_json["nets"].keys()),
            "Net names don't match"
        )
        
        # For each net, compare node count
        for net_name in expected_json["nets"]:
            self.assertEqual(
                # Structure A: Access the list directly
                len(actual_json["nets"][net_name]),
                # Assuming expected_json also uses Structure A (or needs updating)
                len(expected_json["nets"][net_name]),
                f"Node count for net {net_name} doesn't match"
            )
        
        # Check subcircuit count
        self.assertEqual(
            len(actual_json["subcircuits"]),
            len(expected_json["subcircuits"]),
            "Subcircuit count doesn't match"
        )


if __name__ == "__main__":
    unittest.main()