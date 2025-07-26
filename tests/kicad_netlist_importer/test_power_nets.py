"""
Unit tests for the KiCad netlist importer, specifically focused on 
verifying correct parsing of resistor divider networks across multiple sheets.
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

class TestKicadResistorDividerNetlistImporter(unittest.TestCase):
    """
    Tests the KiCad netlist importer against a netlist containing multiple
    resistor divider networks across different hierarchy levels.
    Verifies proper sheet hierarchy, component placement, net distribution,
    and especially power net placement.
    """

    @classmethod
    def setUpClass(cls):
        # Adjust the BASE_DIR relative to your project layout
        cls.BASE_DIR = Path(__file__).parent.parent

        # The test_data directory that holds netlist files
        cls.NETLIST_PATH = cls.BASE_DIR / "test_data" / "kicad9" / "netlists" / "netlist8.net"

        # Where we store the JSON output
        cls.OUTPUT_DIR = cls.BASE_DIR / "test_output"
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        cls.OUTPUT_JSON = cls.OUTPUT_DIR / "netlist8_output.json"

    def test_import_resistor_divider_netlist(self):
        """
        Test that the netlist8.net file (containing resistor divider networks)
        is correctly converted into the Circuit-Synth JSON format. Verifies:
        1) File presence
        2) Top-level JSON structure
        3) Sheet hierarchy (main, divider, div2, div3)
        4) Components in each subcircuit
        5) Proper net distribution (global nets vs. local nets)
        6) Verification of resistor divider networks
        7) Properties
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

        # -------- Hierarchy Tests --------
        # We expect 3 subcircuits: divider, div2, div3
        subcircuits = data["subcircuits"]
        self.assertEqual(len(subcircuits), 3, 
                        "Expected exactly 3 first-level subcircuits: divider, div2, div3")

        # Helper function to find a subcircuit by name
        def find_subcircuit(subckt_list, name):
            """Helper: Find a subcircuit by name"""
            for s in subckt_list:
                if s["name"] == name:
                    return s
            return None

        # Find all three subcircuits
        divider_subckt = find_subcircuit(subcircuits, "divider")
        div2_subckt = find_subcircuit(subcircuits, "div2")  
        div3_subckt = find_subcircuit(subcircuits, "div3")

        self.assertIsNotNone(divider_subckt, "Subcircuit 'divider' should exist")
        self.assertIsNotNone(div2_subckt, "Subcircuit 'div2' should exist")
        self.assertIsNotNone(div3_subckt, "Subcircuit 'div3' should exist")

        # Check that subcircuits don't have further nesting
        self.assertEqual(len(divider_subckt.get("subcircuits", [])), 0, "divider should not have child subcircuits")
        self.assertEqual(len(div2_subckt.get("subcircuits", [])), 0, "div2 should not have child subcircuits")
        self.assertEqual(len(div3_subckt.get("subcircuits", [])), 0, "div3 should not have child subcircuits")

        # -------- Component Tests --------
        # Check root components
        root_components = data["components"]
        self.assertIn("R1", root_components, "R1 should exist in root circuit")
        self.assertIn("R2", root_components, "R2 should exist in root circuit")
        self.assertEqual(root_components["R1"]["value"], "10k", "R1 value should be 10k")
        self.assertEqual(root_components["R2"]["value"], "3k", "R2 value should be 3k")
        self.assertEqual(root_components["R1"]["footprint"], "Resistor_SMD:R_0603_1608Metric")
        self.assertEqual(root_components["R2"]["footprint"], "Resistor_SMD:R_0603_1608Metric")

        # Check divider components (R3, R4, R5)
        divider_components = divider_subckt["components"]
        self.assertIn("R3", divider_components, "R3 should exist in divider subcircuit")
        self.assertIn("R4", divider_components, "R4 should exist in divider subcircuit")
        self.assertIn("R5", divider_components, "R5 should exist in divider subcircuit")
        self.assertEqual(divider_components["R3"]["value"], "10k", "R3 value should be 10k")
        self.assertEqual(divider_components["R4"]["value"], "3k", "R4 value should be 3k")
        self.assertEqual(divider_components["R5"]["value"], "0R", "R5 value should be 0R")

        # Check div2 components (R6, R7, R8)
        div2_components = div2_subckt["components"]
        self.assertIn("R6", div2_components, "R6 should exist in div2 subcircuit")
        self.assertIn("R7", div2_components, "R7 should exist in div2 subcircuit")
        self.assertIn("R8", div2_components, "R8 should exist in div2 subcircuit")
        self.assertEqual(div2_components["R6"]["value"], "0R", "R6 value should be 0R")
        self.assertEqual(div2_components["R7"]["value"], "10k", "R7 value should be 10k")
        self.assertEqual(div2_components["R8"]["value"], "3k", "R8 value should be 3k")

        # Check div3 components (R9, R10, R11)
        div3_components = div3_subckt["components"]
        self.assertIn("R9", div3_components, "R9 should exist in div3 subcircuit")
        self.assertIn("R10", div3_components, "R10 should exist in div3 subcircuit")
        self.assertIn("R11", div3_components, "R11 should exist in div3 subcircuit")
        self.assertEqual(div3_components["R9"]["value"], "0R", "R9 value should be 0R")
        self.assertEqual(div3_components["R10"]["value"], "10k", "R10 value should be 10k")
        self.assertEqual(div3_components["R11"]["value"], "3k", "R11 value should be 3k")

        # Ensure no components appear in the wrong subcircuit
        self.assertNotIn("R3", root_components, "R3 should not be in root circuit")
        self.assertNotIn("R6", root_components, "R6 should not be in root circuit")
        self.assertNotIn("R9", root_components, "R9 should not be in root circuit")
        self.assertNotIn("R1", divider_components, "R1 should not be in divider subcircuit")
        self.assertNotIn("R6", divider_components, "R6 should not be in divider subcircuit")
        self.assertNotIn("R1", div2_components, "R1 should not be in div2 subcircuit")
        self.assertNotIn("R3", div2_components, "R3 should not be in div2 subcircuit")
        self.assertNotIn("R1", div3_components, "R1 should not be in div3 subcircuit")
        self.assertNotIn("R3", div3_components, "R3 should not be in div3 subcircuit")
        self.assertNotIn("R6", div3_components, "R6 should not be in div3 subcircuit")

        # -------- Net Tests --------
        # Check global nets (GND should appear in all subcircuits)
        root_nets = data["nets"]
        divider_nets = divider_subckt["nets"]
        div2_nets = div2_subckt["nets"]
        div3_nets = div3_subckt["nets"]

        # Check global power nets presence
        self.assertIn("GND", root_nets, "GND should exist in root circuit")
        self.assertIn("GND", divider_nets, "GND should exist in divider subcircuit")
        self.assertIn("GND", div2_nets, "GND should exist in div2 subcircuit")
        self.assertIn("GND", div3_nets, "GND should exist in div3 subcircuit")

        # Check power nets that should be limited to specific subcircuits
        self.assertIn("+3V3", root_nets, "+3V3 should exist in root circuit")
        self.assertIn("+5V", divider_nets, "+5V should exist in divider subcircuit")
        self.assertIn("+1V8", div2_nets, "+1V8 should exist in div2 subcircuit")
        self.assertIn("+12LF", div3_nets, "+12LF should exist in div3 subcircuit")

        # Verify power nets are NOT in wrong subcircuits
        self.assertNotIn("+5V", root_nets, "+5V should NOT exist in root circuit")
        self.assertNotIn("+1V8", root_nets, "+1V8 should NOT exist in root circuit")
        self.assertNotIn("+12LF", root_nets, "+12LF should NOT exist in root circuit")
        self.assertNotIn("+3V3", divider_nets, "+3V3 should NOT exist in divider subcircuit")
        self.assertNotIn("+1V8", divider_nets, "+1V8 should NOT exist in divider subcircuit")
        self.assertNotIn("+12LF", divider_nets, "+12LF should NOT exist in divider subcircuit")
        self.assertNotIn("+3V3", div2_nets, "+3V3 should NOT exist in div2 subcircuit")
        self.assertNotIn("+5V", div2_nets, "+5V should NOT exist in div2 subcircuit")
        self.assertNotIn("+12LF", div2_nets, "+12LF should NOT exist in div2 subcircuit")
        self.assertNotIn("+3V3", div3_nets, "+3V3 should NOT exist in div3 subcircuit")
        self.assertNotIn("+5V", div3_nets, "+5V should NOT exist in div3 subcircuit")
        self.assertNotIn("+1V8", div3_nets, "+1V8 should NOT exist in div3 subcircuit")

        # Check hierarchical nets that indicate voltage divider outputs
        # UPDATED: Use flattened net names (without leading slashes or hierarchy path)
        self.assertIn("vout1", root_nets, "vout1 should exist in root circuit")
        self.assertIn("vout5v", divider_nets, "vout5v should exist in divider subcircuit") 
        self.assertIn("vout1v8", div2_nets, "vout1v8 should exist in div2 subcircuit")
        self.assertIn("vout12v", div3_nets, "vout12v should exist in div3 subcircuit")

        # Verify hierarchical nets are not leaked to other subcircuits
        # UPDATED: Use flattened net names (without leading slashes or hierarchy path)
        self.assertNotIn("vout5v", root_nets, "vout5v should NOT exist in root circuit")
        self.assertNotIn("vout1v8", root_nets, "vout1v8 should NOT exist in root circuit")
        self.assertNotIn("vout12v", root_nets, "vout12v should NOT exist in root circuit")
        self.assertNotIn("vout1", divider_nets, "vout1 should NOT exist in divider subcircuit")
        self.assertNotIn("vout1v8", divider_nets, "vout1v8 should NOT exist in divider subcircuit")
        self.assertNotIn("vout12v", divider_nets, "vout12v should NOT exist in divider subcircuit")
        self.assertNotIn("vout1", div2_nets, "vout1 should NOT exist in div2 subcircuit")
        self.assertNotIn("vout5v", div2_nets, "vout5v should NOT exist in div2 subcircuit")
        self.assertNotIn("vout12v", div2_nets, "vout12v should NOT exist in div2 subcircuit")
        self.assertNotIn("vout1", div3_nets, "vout1 should NOT exist in div3 subcircuit")
        self.assertNotIn("vout5v", div3_nets, "vout5v should NOT exist in div3 subcircuit")
        self.assertNotIn("vout1v8", div3_nets, "vout1v8 should NOT exist in div3 subcircuit")

        # -------- Specific Net Connectivity Tests --------
        # UPDATED: Use flattened net names in the helper function calls
        # Test resistor divider in root circuit (R1-R2)
        self.assertTrue(self._check_resistor_divider(
            root_nets, "R1", "R2", "+3V3", "vout1", "GND"
        ), "Root resistor divider network (R1-R2) is incorrectly connected")

        # Test resistor divider in divider subcircuit (R3-R4)
        self.assertTrue(self._check_resistor_divider(
            divider_nets, "R3", "R4", "+5V_div1", "vout5v", "GND"
        ), "Divider subcircuit resistor divider (R3-R4) is incorrectly connected")

        # Test jumper in divider subcircuit (R5)
        self.assertTrue(self._check_jumper(
            divider_nets, "R5", "+5V", "+5V_div1"
        ), "Jumper R5 in divider subcircuit is incorrectly connected")

        # Test resistor divider in div2 subcircuit (R7-R8)
        self.assertTrue(self._check_resistor_divider(
            div2_nets, "R7", "R8", "+1V8", "vout1v8", "GND"
        ), "Div2 subcircuit resistor divider (R7-R8) is incorrectly connected")

        # Test jumper in div2 subcircuit (R6)
        self.assertTrue(self._check_jumper(
            div2_nets, "R6", "+1V8", "+1V8"
        ), "Jumper R6 in div2 subcircuit is incorrectly connected")

        # Test resistor divider in div3 subcircuit (R10-R11)
        self.assertTrue(self._check_resistor_divider(
            div3_nets, "R10", "R11", "+12_out", "vout12v", "GND"
        ), "Div3 subcircuit resistor divider (R10-R11) is incorrectly connected")

        # Test jumper in div3 subcircuit (R9)
        self.assertTrue(self._check_jumper(
            div3_nets, "R9", "+12LF", "+12_out"
        ), "Jumper R9 in div3 subcircuit is incorrectly connected")

        # -------- Properties Tests --------
        self.assertIn("source", data["properties"], "Missing 'source' property")
        self.assertIn("date", data["properties"], "Missing 'date' property")
        self.assertIn("tool", data["properties"], "Missing 'tool' property")
        self.assertEqual("Eeschema 8.0.8", data["properties"]["tool"], "Tool should be Eeschema 8.0.8")

        logger.info(f"Resistor divider netlist => JSON output written to: {self.OUTPUT_JSON.resolve()}")
    def _check_resistor_divider(self, nets, r_top_name, r_bottom_name, in_net_name, middle_net_name, out_net_name):
        """
        Helper method to check a resistor divider network's connectivity
        
        Parameters:
        - nets: Dictionary of nets
        - r_top_name: Name of the top resistor
        - r_bottom_name: Name of the bottom resistor
        - in_net_name: Name of the input voltage net
        - middle_net_name: Name of the middle net (divider output)
        - out_net_name: Name of the output net (usually GND)
        
        Returns: True if the divider is properly connected, False otherwise
        """
        # Check top resistor connection to input net
        r_top_in_connected = False
        if in_net_name in nets:
            # Structure A: nets[in_net_name] is the list of nodes
            for node in nets[in_net_name]:
                if node["component"] == r_top_name and node["pin"]["number"] == "1":
                    r_top_in_connected = True
                    break
        
        # Check top resistor connection to middle net
        r_top_middle_connected = False
        if middle_net_name in nets:
            # Structure A: nets[middle_net_name] is the list of nodes
            for node in nets[middle_net_name]:
                if node["component"] == r_top_name and node["pin"]["number"] == "2":
                    r_top_middle_connected = True
                    break
        
        # Check bottom resistor connection to middle net
        r_bottom_middle_connected = False
        if middle_net_name in nets:
            # Structure A: nets[middle_net_name] is the list of nodes
            for node in nets[middle_net_name]:
                if node["component"] == r_bottom_name and node["pin"]["number"] == "1":
                    r_bottom_middle_connected = True
                    break
        
        # Check bottom resistor connection to output net
        r_bottom_out_connected = False
        if out_net_name in nets:
            # Structure A: nets[out_net_name] is the list of nodes
            for node in nets[out_net_name]:
                if node["component"] == r_bottom_name and node["pin"]["number"] == "2":
                    r_bottom_out_connected = True
                    break
        
        return (r_top_in_connected and r_top_middle_connected and 
                r_bottom_middle_connected and r_bottom_out_connected)

    def _check_jumper(self, nets, jumper_name, in_net_name, out_net_name):
        """
        Helper method to check a jumper (0R resistor) connectivity
        
        Parameters:
        - nets: Dictionary of nets
        - jumper_name: Name of the jumper resistor
        - in_net_name: Name of the input net
        - out_net_name: Name of the output net
        
        Returns: True if the jumper is properly connected, False otherwise
        """
        # Check jumper connection to input net
        jumper_in_connected = False
        if in_net_name in nets:
            # Structure A: nets[in_net_name] is the list of nodes
            for node in nets[in_net_name]:
                if node["component"] == jumper_name and node["pin"]["number"] == "1":
                    jumper_in_connected = True
                    break
        
        # Check jumper connection to output net
        jumper_out_connected = False
        if out_net_name in nets:
            # Structure A: nets[out_net_name] is the list of nodes
            for node in nets[out_net_name]:
                if node["component"] == jumper_name and node["pin"]["number"] == "2":
                    jumper_out_connected = True
                    break
        
        return jumper_in_connected and jumper_out_connected


if __name__ == "__main__":
    unittest.main()