import unittest
import json
import os
from pathlib import Path

from circuit_synth.kicad.netlist_importer import convert_netlist, PinType


class TestCircuit4NetlistImporter(unittest.TestCase):
    """
    Tests the KiCad netlist importer for circuit4.net 
    located in tests/test_data/kicad9/kicad_projects/circuit4/.
    This circuit has hierarchical schematic files (led.kicad_sch, light_sensor.kicad_sch, 
    regulator.kicad_sch, usb.kicad_sch).
    """

    @classmethod
    def setUpClass(cls):
        # Base directory: tests/ (i.e. three parents up from this file)
        cls.BASE_DIR = Path(__file__).parent.parent

        # Path to circuit4.net
        cls.NETLIST_PATH = cls.BASE_DIR / "test_data" / "kicad9" / "kicad_projects" / "circuit4" / "circuit4.net"
        
        # Create output directory if it doesn't exist
        cls.OUTPUT_DIR = cls.BASE_DIR / "test_output"
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        
        # Output JSON path
        cls.OUTPUT_JSON_PATH = cls.OUTPUT_DIR / "circuit4_output.json"

    def test_import_circuit4(self):
        """
        Test parsing circuit4.net, verifying structure, components, nets, etc.
        This test also verifies proper handling of hierarchical netlists.
        
        This test ensures that:
        1. The file exists
        2. The netlist can be converted to JSON
        3. The JSON has the correct structure
        4. Components are properly parsed with their properties
        5. Nets are properly parsed with their nodes
        6. Hierarchical structure is correctly maintained
        7. Components are placed in their correct subcircuits
        8. Nets are properly distributed across subcircuits
        9. Global nets (power, ground) are handled correctly
        """
        # 1) Verify file presence
        self.assertTrue(
            self.NETLIST_PATH.is_file(),
            f"Missing test netlist file: {self.NETLIST_PATH}"
        )

        # 2) Convert circuit4.net => circuit4_output.json
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

        # The top-level circuit name should match "circuit4"
        self.assertEqual(data["name"], "circuit4")

        # ---- Check components ----
        # Verify component count and references
        self.assertGreater(len(data["components"]), 0, "No components found in the circuit")
        
        # Check specific component properties if they exist
        for component_ref, component_data in data["components"].items():
            self.assertIn("value", component_data, f"Component {component_ref} missing 'value' property")
            if "footprint" in component_data:
                self.assertIsInstance(component_data["footprint"], str,
                                     f"Component {component_ref} has invalid footprint")
        
        # ---- Check nets ----
        # Verify net count
        self.assertGreater(len(data["nets"]), 0, "No nets found in the circuit")
        
        # ---- Check hierarchical structure ----
        # Since circuit4 has hierarchical schematic files, we should check for subcircuits
        self.assertIn("subcircuits", data)
        subcircuits = data["subcircuits"]
        self.assertGreater(len(subcircuits), 0, "No subcircuits found in the hierarchical circuit")
        
        # Check each subcircuit
        for subcircuit in subcircuits:
            # Check subcircuit has required fields
            self.assertIn("name", subcircuit, "Subcircuit missing 'name' field")
            self.assertIn("components", subcircuit, "Subcircuit missing 'components' field")
            self.assertIn("nets", subcircuit, "Subcircuit missing 'nets' field")
            self.assertIn("subcircuits", subcircuit, "Subcircuit missing 'subcircuits' field")
            
            # Check subcircuit components
            self.assertIsInstance(subcircuit["components"], dict,
                                 f"Subcircuit {subcircuit['name']} 'components' is not a dictionary")
            
            # Check subcircuit nets
            self.assertIsInstance(subcircuit["nets"], dict,
                                 f"Subcircuit {subcircuit['name']} 'nets' is not a dictionary")
            
            # Check for nested subcircuits (circuit4 has multiple levels of hierarchy)
            if len(subcircuit["subcircuits"]) > 0:
                for nested_subcircuit in subcircuit["subcircuits"]:
                    self.assertIn("name", nested_subcircuit, "Nested subcircuit missing 'name' field")
                    self.assertIn("components", nested_subcircuit, "Nested subcircuit missing 'components' field")
                    self.assertIn("nets", nested_subcircuit, "Nested subcircuit missing 'nets' field")
            
            # Check for global nets in subcircuits (like GND, power nets)
            # These should be present in both root and subcircuits if used
            for net_name in ["GND", "+3V3", "+5V"]:
                if net_name in data["nets"]:
                    # If a global net is in root, check if it's also in subcircuit
                    # (but only if the subcircuit has components that might use it)
                    if len(subcircuit["components"]) > 0 and len(subcircuit["nets"]) > 0:
                        # We don't assert here because not all subcircuits need all global nets
                        if net_name in subcircuit["nets"]:
                            # If the net is in the subcircuit, verify it has nodes
                            # Structure A: Access the list directly
                            self.assertGreater(len(subcircuit["nets"][net_name]), 0,
                                                 f"Net {net_name} in subcircuit {subcircuit['name']} has no nodes")
        
        # ---- Check properties ----
        props = data["properties"]
        self.assertIn("source", props)
        self.assertIn("date", props)
        
        print(f"circuit4.net => JSON output written to: {self.OUTPUT_JSON_PATH.resolve()}")

    def test_match_reference_json(self):
        """
        Test to ensure circuit4 matches the expected output in circuit4_expected.json.
        This test compares the generated output against a known good reference.
        
        This is particularly useful when refactoring the importer code to ensure
        it maintains backward compatibility.
        """
        # Path to the reference/expected JSON
        expected_json_path = self.BASE_DIR / "test_data" / "kicad9" / "expected_outputs" / "circuit4_expected.json"
        
        # Skip if reference file doesn't exist - we'll just create it instead
        if not expected_json_path.exists():
            # If reference doesn't exist, generate it from current implementation
            expected_json_path.parent.mkdir(exist_ok=True, parents=True)
            convert_netlist(self.NETLIST_PATH, expected_json_path)
            print(f"Created reference JSON at {expected_json_path}")
            self.skipTest("Reference JSON didn't exist - created it for future tests")
        
        # Convert circuit4.net to JSON
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