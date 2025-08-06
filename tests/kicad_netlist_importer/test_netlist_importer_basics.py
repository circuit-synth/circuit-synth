import json
import os
import unittest
from pathlib import Path

from circuit_synth.kicad.netlist_importer import PinType, convert_netlist


class TestKicadNetlistImporter(unittest.TestCase):
    """
    Tests the KiCad netlist importer for netlist1.net and netlist2.net
    located in tests/test_data/kicad9/netlists/.
    """

    @classmethod
    def setUpClass(cls):
        # Base directory: tests/ (i.e. three parents up from this file)
        cls.BASE_DIR = Path(__file__).parent.parent

        # Paths to netlist1.net and netlist2.net
        cls.NETLIST1_PATH = (
            cls.BASE_DIR / "test_data" / "kicad9" / "netlists" / "netlist1.net"
        )
        cls.NETLIST2_PATH = (
            cls.BASE_DIR / "test_data" / "kicad9" / "netlists" / "netlist2.net"
        )

        # Create output directory if it doesn't exist
        cls.OUTPUT_DIR = cls.BASE_DIR / "test_output"
        cls.OUTPUT_DIR.mkdir(exist_ok=True)

        # Output JSON paths
        cls.OUTPUT1_JSON_PATH = cls.OUTPUT_DIR / "netlist1_output.json"
        cls.OUTPUT2_JSON_PATH = cls.OUTPUT_DIR / "netlist2_output.json"

    def test_import_netlist1(self):
        """
        Test parsing netlist1.net, verifying structure, components, nets, etc.
        """
        # 1) Verify file presence
        self.assertTrue(
            self.NETLIST1_PATH.is_file(),
            f"Missing test netlist file: {self.NETLIST1_PATH}",
        )

        # 2) Convert netlist1.net => netlist1_output.json
        convert_netlist(self.NETLIST1_PATH, self.OUTPUT1_JSON_PATH)
        self.assertTrue(self.OUTPUT1_JSON_PATH.exists())

        # 3) Load the JSON and check structure
        with self.OUTPUT1_JSON_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # ---- Basic top-level checks ----
        self.assertIn("name", data)
        self.assertIn("components", data)
        self.assertIn("nets", data)
        self.assertIn("subcircuits", data)
        self.assertIn("properties", data)

        # The top-level circuit name should match "netlist1"
        self.assertEqual(data["name"], "netlist1")

        # ---- Check components ----
        expected_refs = {"C1", "R1", "R2"}
        self.assertEqual(set(data["components"].keys()), expected_refs)
        self.assertEqual(data["components"]["C1"]["value"], "0.1uF")
        self.assertEqual(data["components"]["R1"]["value"], "10k")
        self.assertEqual(data["components"]["R2"]["value"], "1k")

        # ---- Check nets ----
        expected_nets = {"+3V3", "OUTPUT", "GND"}
        self.assertEqual(set(data["nets"].keys()), expected_nets)

        # Structure A: Access list directly
        self.assertEqual(len(data["nets"]["+3V3"]), 1)
        # Note: 'code' is no longer part of the standardized 'nets' structure

        # Structure A: Access list directly
        self.assertEqual(len(data["nets"]["OUTPUT"]), 3)
        # Note: 'code' is no longer part of the standardized 'nets' structure

        # Structure A: Access list directly
        self.assertEqual(len(data["nets"]["GND"]), 2)
        # Note: 'code' is no longer part of the standardized 'nets' structure

        # ---- Check subcircuits (none expected) ----
        self.assertEqual(len(data["subcircuits"]), 0)

        # ---- Check properties ----
        props = data["properties"]
        self.assertIn("source", props)
        self.assertIn("date", props)
        self.assertEqual(props.get("tool"), "Eeschema 8.0.8")

        print(
            f"netlist1.net => JSON output written to: {self.OUTPUT1_JSON_PATH.resolve()}"
        )

    def test_import_netlist2(self):
        """
        Test parsing netlist2.net, verifying structure, components, nets, pin types, etc.
        Tests proper handling of different pin types, including:
        - power_in, power_out, input, output, bidirectional, passive, no_connect
        - Components including microcontroller, LEDs, resistors, and unconnected pins
        """
        # 1) Verify file presence
        self.assertTrue(
            self.NETLIST2_PATH.is_file(),
            f"Missing test netlist file: {self.NETLIST2_PATH}",
        )

        # 2) Convert netlist2.net => netlist2_output.json
        convert_netlist(self.NETLIST2_PATH, self.OUTPUT2_JSON_PATH)
        self.assertTrue(self.OUTPUT2_JSON_PATH.exists())

        # 3) Load the JSON and check structure
        with self.OUTPUT2_JSON_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # ---- Basic top-level checks ----
        self.assertIn("name", data)
        self.assertIn("components", data)
        self.assertIn("nets", data)
        self.assertIn("subcircuits", data)
        self.assertIn("properties", data)

        # The top-level circuit name should match "netlist2"
        self.assertEqual(data["name"], "netlist2")

        # ---- Check components ----
        expected_components = {"D1", "R1", "U1"}
        self.assertEqual(set(data["components"].keys()), expected_components)

        # Verify component details
        self.assertEqual(data["components"]["D1"]["value"], "LED")
        self.assertEqual(
            data["components"]["D1"]["footprint"], "LED_SMD:LED_0603_1608Metric"
        )
        self.assertEqual(
            data["components"]["D1"]["description"], "Light emitting diode"
        )

        self.assertEqual(data["components"]["R1"]["value"], "10k")
        self.assertEqual(
            data["components"]["R1"]["footprint"], "Resistor_SMD:R_0603_1608Metric"
        )
        self.assertEqual(data["components"]["R1"]["description"], "Resistor")

        self.assertEqual(data["components"]["U1"]["value"], "ESP32-C6-MINI-1")
        self.assertEqual(
            data["components"]["U1"]["footprint"], "RF_Module:ESP32-C6-MINI-1"
        )
        self.assertTrue(
            "RF Module, ESP32-C6 SoC" in data["components"]["U1"]["description"]
        )

        # ---- Check nets ----
        # We should have 33 nets in total for netlist2.net
        self.assertEqual(len(data["nets"]), 33)

        # Check important nets and their nodes
        self.assertIn("+3V3", data["nets"])
        # Structure A: Access list directly
        self.assertEqual(len(data["nets"]["+3V3"]), 1)
        # Note: 'code' is no longer part of the standardized 'nets' structure
        self.assertEqual(data["nets"]["+3V3"][0]["component"], "U1")  # Structure A
        self.assertEqual(data["nets"]["+3V3"][0]["pin"]["number"], "3")  # Structure A
        self.assertEqual(
            data["nets"]["+3V3"][0]["pin"]["type"], "power_in"
        )  # Structure A

        self.assertIn("GND", data["nets"])
        # Structure A: Access list directly
        # Should have 23 nodes in GND (1 for D1 and 22 for U1)
        self.assertEqual(len(data["nets"]["GND"]), 23)
        # Note: 'code' is no longer part of the standardized 'nets' structure

        self.assertIn("Net-(D1-A)", data["nets"])
        # Structure A: Access list directly
        self.assertEqual(len(data["nets"]["Net-(D1-A)"]), 2)
        # Note: 'code' is no longer part of the standardized 'nets' structure

        self.assertIn("Net-(U1-IO12)", data["nets"])
        # Structure A: Access list directly
        self.assertEqual(len(data["nets"]["Net-(U1-IO12)"]), 2)
        # Note: 'code' is no longer part of the standardized 'nets' structure

        # ---- Check pin types ----
        # Verify various pin types are correctly parsed
        pin_types_found = set()

        for net_name, net_data in data["nets"].items():
            # Structure A: net_data is the list of nodes
            for node in net_data:
                pin_type = node["pin"]["type"]
                pin_types_found.add(pin_type)

                # Check specific pins for correct types
                if node["component"] == "U1" and node["pin"]["number"] == "3":
                    self.assertEqual(pin_type, "power_in")
                elif node["component"] == "U1" and node["pin"]["number"] == "8":
                    self.assertEqual(pin_type, "input")
                elif node["component"] == "U1" and node["pin"]["number"] == "17":
                    self.assertEqual(pin_type, "bidirectional")
                elif node["component"] == "D1" and node["pin"]["number"] in ["1", "2"]:
                    self.assertEqual(pin_type, "passive")
                elif node["component"] == "U1" and node["pin"]["number"] == "4":
                    # no_connect pins are mapped to unspecified in PinType enum
                    self.assertEqual(pin_type, "unspecified")

        # Verify we found various pin types
        expected_pin_types = {
            "power_in",
            "input",
            "bidirectional",
            "passive",
            "unspecified",
        }
        self.assertTrue(
            expected_pin_types.issubset(pin_types_found),
            f"Expected pin types {expected_pin_types} but found {pin_types_found}",
        )

        # ---- Check unconnected pins ----
        # Verify unconnected pins are properly handled
        unconnected_nets = [
            net for net in data["nets"] if net.startswith("unconnected-")
        ]
        self.assertGreaterEqual(
            len(unconnected_nets), 5
        )  # Should have multiple unconnected nets

        # Check NC pins specifically
        nc_pins = [net for net in unconnected_nets if "NC-Pad" in net]
        self.assertEqual(len(nc_pins), 7)  # U1 has 7 NC pins

        # ---- Check subcircuits (none expected) ----
        self.assertEqual(len(data["subcircuits"]), 0)

        # ---- Check properties ----
        props = data["properties"]
        self.assertIn("source", props)
        self.assertIn("date", props)
        self.assertEqual(props.get("tool"), "Eeschema 8.0.8")

        print(
            f"netlist2.net => JSON output written to: {self.OUTPUT2_JSON_PATH.resolve()}"
        )

    def test_match_reference_json(self):
        """
        Test to ensure netlist2 matches the expected output in netlist2_output.json.
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
            / "netlist2_expected.json"
        )

        # Skip if reference file doesn't exist - we'll just create it instead
        if not expected_json_path.exists():
            # If reference doesn't exist, generate it from current implementation
            expected_json_path.parent.mkdir(exist_ok=True, parents=True)
            convert_netlist(self.NETLIST2_PATH, expected_json_path)
            print(f"Created reference JSON at {expected_json_path}")
            self.skipTest("Reference JSON didn't exist - created it for future tests")

        # Convert netlist2.net to JSON
        convert_netlist(self.NETLIST2_PATH, self.OUTPUT2_JSON_PATH)

        # Load both files
        with self.OUTPUT2_JSON_PATH.open("r", encoding="utf-8") as f:
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
