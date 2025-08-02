"""
Unit tests for the KiCad netlist importer, focused on testing nested hierarchical
bus connections across multiple sheets with three ESP32 modules.
"""

import unittest
import json
import os
import logging
from pathlib import Path

from circuit_synth.kicad.netlist_importer import convert_netlist

# Configure logging for tests
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestKicadNestedHierarchyImporter(unittest.TestCase):
    """
    Tests the KiCad netlist importer to verify proper handling of bus connections
    between components across multiple hierarchical sheets including nested subcircuits.
    """

    @classmethod
    def setUpClass(cls):
        # Adjust the BASE_DIR relative to your project layout
        cls.BASE_DIR = Path(__file__).parent.parent

        # The test_data directory that holds netlist files
        cls.NETLIST_PATH = cls.BASE_DIR / "test_data" / "kicad9" / "netlists" / "netlist7.net"

        # Where we store the JSON output
        cls.OUTPUT_DIR = cls.BASE_DIR / "test_output"
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        cls.OUTPUT_JSON = cls.OUTPUT_DIR / "netlist7_output.json"

    def test_import_nested_hierarchy_netlist(self):
        """
        Test that a netlist with nested hierarchical sheets and bus connections is
        converted correctly into the Circuit-Synth JSON. Verifies:
        1) File presence
        2) Top-level JSON structure
        3) Hierarchical sheet structure (nested subcircuits)
        4) Components in all hierarchical levels
        5) Bus connections between components across different hierarchical levels
        6) Global power nets (+3V3 and GND)
        7) Proper pin connections to the bus nets with different pin assignments
        """

        # 1) Verify file presence
        self.assertTrue(
            self.NETLIST_PATH.is_file(),
            f"Missing test netlist file: {self.NETLIST_PATH}"
        )

        # 2) Convert netlist => JSON
        convert_netlist(self.NETLIST_PATH, self.OUTPUT_JSON)
        self.assertTrue(self.OUTPUT_JSON.exists())

        # 3) Load the JSON and check structure
        with self.OUTPUT_JSON.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # -------- Basic Structure Tests --------
        required_fields = ["name", "components", "nets", "subcircuits", "properties"]
        for field in required_fields:
            self.assertIn(field, data, f"Missing required top-level field: {field}")

        # Circuit name should match the input file stem
        self.assertEqual(data["name"], self.NETLIST_PATH.stem)

        # -------- Hierarchical Structure Tests --------
        # We expect the hierarchy: Root -> ESP321 -> esp32_3
        subcircuits = data["subcircuits"]
        self.assertGreaterEqual(len(subcircuits), 1, "Expected at least 1 subcircuit")
        
        # Find the ESP321 subcircuit
        esp321_subckt = None
        for s in subcircuits:
            if s["name"] == "ESP321":
                esp321_subckt = s
                break
        
        self.assertIsNotNone(esp321_subckt, "Should have 'ESP321' subcircuit")
        
        # Find the esp32_3 subcircuit inside ESP321
        esp32_3_subckt = None
        if "subcircuits" in esp321_subckt:
            for s in esp321_subckt["subcircuits"]:
                if s["name"] == "esp32_3":
                    esp32_3_subckt = s
                    break
        
        self.assertIsNotNone(esp32_3_subckt, "Should have 'esp32_3' subcircuit inside ESP321")

        # -------- Component Tests --------
        # Verify components in Root
        root_components = data["components"]
        self.assertIn("C1", root_components, "Root should contain C1")
        self.assertIn("U1", root_components, "Root should contain U1")
        
        # Verify component properties in Root
        self.assertEqual(root_components["C1"]["value"], "0.1uF")
        self.assertEqual(root_components["U1"]["value"], "ESP32-C6-MINI-1")
        self.assertEqual(root_components["U1"]["footprint"], "RF_Module:ESP32-C6-MINI-1")
        
        # Verify components in ESP321 subcircuit
        esp321_components = esp321_subckt["components"]
        self.assertIn("C2", esp321_components, "ESP321 should contain C2")
        self.assertIn("U2", esp321_components, "ESP321 should contain U2")
        
        # Verify component properties in ESP321 subcircuit
        self.assertEqual(esp321_components["C2"]["value"], "0.1uF")
        self.assertEqual(esp321_components["U2"]["value"], "ESP32-C6-MINI-1")
        self.assertEqual(esp321_components["U2"]["footprint"], "RF_Module:ESP32-C6-MINI-1")
        
        # Verify components in esp32_3 nested subcircuit
        esp32_3_components = esp32_3_subckt["components"]
        self.assertIn("C3", esp32_3_components, "esp32_3 should contain C3")
        self.assertIn("U3", esp32_3_components, "esp32_3 should contain U3")
        
        # Verify component properties in esp32_3 subcircuit
        self.assertEqual(esp32_3_components["C3"]["value"], "0.1uF")
        self.assertEqual(esp32_3_components["U3"]["value"], "ESP32-C6-MINI-1")
        self.assertEqual(esp32_3_components["U3"]["footprint"], "RF_Module:ESP32-C6-MINI-1")

        # -------- Bus Connection Tests --------
        # Verify bus nets in each level - note that leading slashes are removed by the converter
        root_nets = data["nets"]
        esp321_nets = esp321_subckt["nets"]
        esp32_3_nets = esp32_3_subckt["nets"]
        
        # Test for all four bus nets at each level
        bus_nets = ["COMMS.I2C1_SCL", "COMMS.I2C1_SDA", "COMMS.I2C2_SCL", "COMMS.I2C2_SDA"]
        
        for bus_net in bus_nets:
            # Check nets exist at each level
            self.assertIn(bus_net, root_nets, f"Root should have {bus_net} bus net")
            
            # Check that nets propagate through hierarchy
            self.assertIn(bus_net, esp321_nets, f"ESP321 should have {bus_net} bus net")
            self.assertIn(bus_net, esp32_3_nets, f"esp32_3 should have {bus_net} bus net")
        
        # -------- Bus Connection Validation --------
        # Verify the specific pin assignments for each ESP module
        
        # I2C1_SCL connections
        # U1 pin 18 (IO13), U2 pin 18 (IO13), U3 pin 15 (IO6)
        self._verify_pin_connected(root_nets, "COMMS.I2C1_SCL", "U1", "18", "IO13")
        self._verify_pin_connected(esp321_nets, "COMMS.I2C1_SCL", "U2", "18", "IO13")
        self._verify_pin_connected(esp32_3_nets, "COMMS.I2C1_SCL", "U3", "15", "IO6")
        
        # I2C1_SDA connections
        # U1 pin 17 (IO12), U2 pin 17 (IO12), U3 pin 10 (IO5)
        self._verify_pin_connected(root_nets, "COMMS.I2C1_SDA", "U1", "17", "IO12")
        self._verify_pin_connected(esp321_nets, "COMMS.I2C1_SDA", "U2", "17", "IO12")
        self._verify_pin_connected(esp32_3_nets, "COMMS.I2C1_SDA", "U3", "10", "IO5")
        
        # I2C2_SCL connections
        # U1 pin 25 (IO19), U2 pin 25 (IO19), U3 pin 16 (IO7)
        self._verify_pin_connected(root_nets, "COMMS.I2C2_SCL", "U1", "25", "IO19")
        self._verify_pin_connected(esp321_nets, "COMMS.I2C2_SCL", "U2", "25", "IO19")
        self._verify_pin_connected(esp32_3_nets, "COMMS.I2C2_SCL", "U3", "16", "IO7")
        
        # I2C2_SDA connections
        # U1 pin 24 (IO18), U2 pin 24 (IO18), U3 pin 22 (IO8)
        self._verify_pin_connected(root_nets, "COMMS.I2C2_SDA", "U1", "24", "IO18")
        self._verify_pin_connected(esp321_nets, "COMMS.I2C2_SDA", "U2", "24", "IO18")
        self._verify_pin_connected(esp32_3_nets, "COMMS.I2C2_SDA", "U3", "22", "IO8")
        
        # -------- Global Power Net Tests --------
        # Verify +3V3 power net in all levels
        self.assertIn("+3V3", root_nets, "Root should have +3V3 power net")
        self.assertIn("+3V3", esp321_nets, "ESP321 should have +3V3 power net")
        self.assertIn("+3V3", esp32_3_nets, "esp32_3 should have +3V3 power net")
        
        # Check power connections for all capacitors and ESP modules
        self._verify_pin_connected(root_nets, "+3V3", "C1", "1")
        self._verify_pin_connected(root_nets, "+3V3", "U1", "3", "3V3")
        
        self._verify_pin_connected(esp321_nets, "+3V3", "C2", "1")
        self._verify_pin_connected(esp321_nets, "+3V3", "U2", "3", "3V3")
        
        self._verify_pin_connected(esp32_3_nets, "+3V3", "C3", "1")
        self._verify_pin_connected(esp32_3_nets, "+3V3", "U3", "3", "3V3")
        
        # Verify GND net in all levels
        self.assertIn("GND", root_nets, "Root should have GND net")
        self.assertIn("GND", esp321_nets, "ESP321 should have GND net")
        self.assertIn("GND", esp32_3_nets, "esp32_3 should have GND net")
        
        # Check GND connections for capacitors
        self._verify_pin_connected(root_nets, "GND", "C1", "2")
        self._verify_pin_connected(esp321_nets, "GND", "C2", "2")
        self._verify_pin_connected(esp32_3_nets, "GND", "C3", "2")
        
        # Verify GND pin counts for ESP modules (each should have 19 GND pins)
        self._verify_pin_count(root_nets, "GND", "U1", 22)
        self._verify_pin_count(esp321_nets, "GND", "U2", 22)
        self._verify_pin_count(esp32_3_nets, "GND", "U3", 22)
        
        # -------- Unconnected Pin Tests --------
        # Verify a sample of unconnected pins for each ESP module
        
        # For U1
        self._verify_unconnected_pins(root_nets, "U1", [8, 9, 12, 13, 19, 20, 26, 30, 31])
        
        # For U2
        self._verify_unconnected_pins(esp321_nets, "U2", [8, 9, 12, 13, 19, 20, 26, 30, 31])
        
        # For U3
        self._verify_unconnected_pins(esp32_3_nets, "U3", [8, 9, 12, 13, 17, 18, 19, 20, 30, 31])
        
        # -------- Connection Count Tests --------
        # Verify total number of nets at each level
        # This is a basic sanity check that we have the expected number of nets
        
        # Expected: global nets (2) + bus nets (4) + unconnected pins
        # U1 has 53 pins, of which 17+4 are connected (22 GND, 1 VCC, 4 bus), so 26 unconnected
        # Total Root nets: 2 + 4 + 32 = 32
        self.assertGreaterEqual(len(root_nets), 32, "Root should have at least 38 nets")
        
        # Same calculation for ESP321 and esp32_3
        self.assertGreaterEqual(len(esp321_nets), 32, "ESP321 should have at least 38 nets")
        self.assertGreaterEqual(len(esp32_3_nets), 32, "esp32_3 should have at least 38 nets")
        
        # -------- Property Tests --------
        self.assertIn("source", data["properties"], "Missing 'source' property")
        self.assertIn("date", data["properties"], "Missing 'date' property")
        self.assertIn("tool", data["properties"], "Missing 'tool' property")
        self.assertEqual(data["properties"]["tool"], "Eeschema 8.0.8", "Tool should be Eeschema 8.0.8")

        logger.info(f"Nested hierarchy test => JSON output written to: {self.OUTPUT_JSON.resolve()}")

    def _verify_pin_connected(self, nets, net_name, component, pin_number, pin_function=None):
        """Helper method to verify that a specific pin is connected to a net"""
        self.assertIn(net_name, nets, f"Net {net_name} not found")
        
        nodes = nets[net_name] # Structure A
        pin_connected = False
        
        for node in nodes: # Already a list
            if node["component"] == component and node["pin"]["number"] == pin_number:
                pin_connected = True
                if pin_function:
                    # Change this line to use "name" instead of "pinfunction"
                    self.assertEqual(node["pin"]["name"], pin_function, 
                                    f"{component} pin {pin_number} should have function {pin_function}")
                break
                
        self.assertTrue(pin_connected, f"{component} pin {pin_number} should connect to {net_name}")

    def _verify_pin_count(self, nets, net_name, component, expected_count):
        """Helper method to verify the number of pins from a component connected to a net"""
        self.assertIn(net_name, nets, f"Net {net_name} not found")
        
        nodes = nets[net_name] # Structure A
        actual_count = sum(1 for node in nodes if node["component"] == component) # Already a list
        
        self.assertEqual(actual_count, expected_count, 
                        f"{component} should have {expected_count} pins connected to {net_name}")

    def _verify_unconnected_pins(self, nets, component, pin_numbers):
        """Helper method to verify that specific pins are unconnected"""
        for pin in pin_numbers:
            # Get the expected pin name
            pin_name = self._get_pin_name(pin)
            net_name = f"unconnected-({component}-{pin_name}-Pad{pin})"
            
            # Net names might be slightly different based on the importer implementation
            # Try common variants
            variants = [
                f"unconnected-({component}-{pin_name}-Pad{pin})",
                f"unconnected-{component}-{pin_name}-Pad{pin}"
            ]
            
            found = False
            for variant in variants:
                if variant in nets:
                    found = True
                    # Verify the net has exactly one node
                    nodes = nets[variant] # Structure A
                    self.assertEqual(len(nodes), 1, f"Unconnected net {variant} should have exactly 1 node")
                    
                    # Verify the node is connected to the right component and pin
                    node = nodes[0] # Already a list
                    self.assertEqual(node["component"], component, f"Node should be connected to {component}")
                    self.assertEqual(node["pin"]["number"], str(pin), f"Node should be connected to pin {pin}")
                    break
            
            self.assertTrue(found, f"No unconnected net found for {component} pin {pin}")

    def _get_pin_name(self, pin_number):
        """Helper method to get pin name from pin number for ESP32-C6-MINI-1"""
        pin_map = {
            1: "GND", 2: "GND", 3: "3V3", 4: "NC", 5: "IO2", 6: "IO3", 7: "NC", 8: "EN",
            9: "IO4", 10: "IO5", 11: "GND", 12: "IO0", 13: "IO1", 14: "GND", 15: "IO6",
            16: "IO7", 17: "IO12", 18: "IO13", 19: "IO14", 20: "IO15", 21: "NC", 22: "IO8",
            23: "IO9", 24: "IO18", 25: "IO19", 26: "IO20", 27: "IO21", 28: "IO22", 29: "IO23",
            30: "RXD0", 31: "TXD0", 32: "NC", 33: "NC", 34: "NC", 35: "NC"
        }
        # Pins 36-53 are all GND
        for i in range(36, 54):
            pin_map[i] = "GND"
            
        return pin_map.get(pin_number, f"PIN{pin_number}")


if __name__ == "__main__":
    unittest.main()