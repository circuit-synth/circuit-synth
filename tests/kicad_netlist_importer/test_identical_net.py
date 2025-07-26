"""
Unit tests for the KiCad netlist importer, specifically focused on 
verifying correct parsing of identical net names in different subcircuits.
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

class TestKicadIdenticalNetNamesImporter(unittest.TestCase):
    """
    Tests the KiCad netlist importer against a netlist with identical net names
    in different subcircuits. Verifies proper hierarchical scoping and isolation
    of nets between different subcircuits.
    """

    @classmethod
    def setUpClass(cls):
        # Adjust the BASE_DIR relative to your project layout
        cls.BASE_DIR = Path(__file__).parent.parent

        # The test_data directory that holds netlist files
        cls.NETLIST_PATH = cls.BASE_DIR / "test_data" / "kicad9" / "netlists" / "netlist6.net"

        # Where we store the JSON output
        cls.OUTPUT_DIR = cls.BASE_DIR / "test_output"
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        cls.OUTPUT_JSON = cls.OUTPUT_DIR / "netlist6_output.json"

    def test_import_identical_nets_netlist(self):
        """
        Test that a netlist with identical net names in different subcircuits is 
        converted correctly into the Circuit-Synth JSON. Verifies:
        1) File presence
        2) Top-level JSON structure
        3) Subcircuit hierarchy and uniqueness
        4) Components in each subcircuit
        5) Net uniqueness and isolation between subcircuits
        6) Global net handling (+3V3 and GND)
        7) Proper connections within each subcircuit
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

        # -------- Subcircuit Hierarchy Tests --------
        # We expect exactly 2 subcircuits: /op-amp/ and /op-amp1/
        subcircuits = data["subcircuits"]
        self.assertEqual(len(subcircuits), 2, "Expected exactly 2 subcircuits")

        # Find the specific subcircuits we know should exist
        def find_subcircuit(subckts, name):
            """Helper: Find a subcircuit by name"""
            for s in subckts:
                if s["name"] == name:
                    return s
            return None

        op_amp_subckt = find_subcircuit(subcircuits, "op-amp")
        op_amp1_subckt = find_subcircuit(subcircuits, "op-amp1")
        
        self.assertIsNotNone(op_amp_subckt, "Should have 'op-amp' subcircuit")
        self.assertIsNotNone(op_amp1_subckt, "Should have 'op-amp1' subcircuit")

        # -------- Component Tests --------
        # Verify components in op-amp subcircuit
        op_amp_components = op_amp_subckt["components"]
        self.assertIn("C1", op_amp_components, "op-amp should contain C1")
        self.assertIn("R1", op_amp_components, "op-amp should contain R1")
        self.assertIn("R2", op_amp_components, "op-amp should contain R2")
        self.assertIn("U1", op_amp_components, "op-amp should contain U1")
        
        # Verify component properties in op-amp subcircuit
        self.assertEqual(op_amp_components["C1"]["value"], "0.1uF")
        self.assertEqual(op_amp_components["R1"]["value"], "10k")
        self.assertEqual(op_amp_components["R2"]["value"], "100k")
        self.assertEqual(op_amp_components["U1"]["footprint"], "Package_TO_SOT_SMD:SOT-23-5")
        
        # Verify components in op-amp1 subcircuit
        op_amp1_components = op_amp1_subckt["components"]
        self.assertIn("C2", op_amp1_components, "op-amp1 should contain C2")
        self.assertIn("R3", op_amp1_components, "op-amp1 should contain R3")
        self.assertIn("R4", op_amp1_components, "op-amp1 should contain R4")
        self.assertIn("U2", op_amp1_components, "op-amp1 should contain U2")
        
        # Verify component properties in op-amp1 subcircuit
        self.assertEqual(op_amp1_components["C2"]["value"], "1uF")
        self.assertEqual(op_amp1_components["R3"]["value"], "10k")
        self.assertEqual(op_amp1_components["R4"]["value"], "100k")
        self.assertEqual(op_amp1_components["U2"]["footprint"], "Package_TO_SOT_SMD:SOT-23-5")

        # -------- Net Uniqueness Tests --------
        
        # Verify op-amp subcircuit nets
        op_amp_nets = op_amp_subckt["nets"]
        self.assertIn("VIN", op_amp_nets, "op-amp should have VIN net")
        self.assertIn("op_amp_out", op_amp_nets, "op-amp should have op_amp_out net")
        self.assertIn("+3V3", op_amp_nets, "op-amp should have +3V3 net (global)")
        self.assertIn("GND", op_amp_nets, "op-amp should have GND net (global)")
        
        # Verify op-amp1 subcircuit nets
        op_amp1_nets = op_amp1_subckt["nets"]
        self.assertIn("VIN", op_amp1_nets, "op-amp1 should have VIN net")
        self.assertIn("op_amp_out", op_amp1_nets, "op-amp1 should have op_amp_out net")
        self.assertIn("+3V3", op_amp1_nets, "op-amp1 should have +3V3 net (global)")
        self.assertIn("GND", op_amp1_nets, "op-amp1 should have GND net (global)")

        # -------- Net Isolation Tests --------
        # Test that VIN nets are separate in each subcircuit
        vin_nodes_1 = op_amp_nets["VIN"] # Structure A
        vin_nodes_2 = op_amp1_nets["VIN"] # Structure A
        
        # VIN in op-amp should connect to U1 pin 1
        u1_vin_connection = False
        for node in vin_nodes_1: # Already a list
            if node["component"] == "U1" and node["pin"]["number"] == "1":
                u1_vin_connection = True
                break
        self.assertTrue(u1_vin_connection, "VIN in op-amp should connect to U1 pin 1")
        
        # VIN in op-amp1 should connect to U2 pin 1
        u2_vin_connection = False
        for node in vin_nodes_2: # Already a list
            if node["component"] == "U2" and node["pin"]["number"] == "1":
                u2_vin_connection = True
                break
        self.assertTrue(u2_vin_connection, "VIN in op-amp1 should connect to U2 pin 1")
        
        # Test that op_amp_out nets are separate in each subcircuit
        out_nodes_1 = op_amp_nets["op_amp_out"] # Structure A
        out_nodes_2 = op_amp1_nets["op_amp_out"] # Structure A
        
        # op_amp_out in op-amp should connect to C1, R2, and U1 output
        c1_connection = False
        r2_connection = False
        u1_out_connection = False
        
        for node in out_nodes_1: # Already a list
            if node["component"] == "C1" and node["pin"]["number"] == "1":
                c1_connection = True
            elif node["component"] == "R2" and node["pin"]["number"] == "2":
                r2_connection = True
            elif node["component"] == "U1" and node["pin"]["number"] == "5":
                u1_out_connection = True
                
        self.assertTrue(c1_connection, "op_amp_out in op-amp should connect to C1 pin 1")
        self.assertTrue(r2_connection, "op_amp_out in op-amp should connect to R2 pin 2")
        self.assertTrue(u1_out_connection, "op_amp_out in op-amp should connect to U1 pin 5")
        
        # op_amp_out in op-amp1 should connect to C2, R4, and U2 output
        c2_connection = False
        r4_connection = False
        u2_out_connection = False
        
        for node in out_nodes_2: # Already a list
            if node["component"] == "C2" and node["pin"]["number"] == "1":
                c2_connection = True
            elif node["component"] == "R4" and node["pin"]["number"] == "2":
                r4_connection = True
            elif node["component"] == "U2" and node["pin"]["number"] == "5":
                u2_out_connection = True
                
        self.assertTrue(c2_connection, "op_amp_out in op-amp1 should connect to C2 pin 1")
        self.assertTrue(r4_connection, "op_amp_out in op-amp1 should connect to R4 pin 2")
        self.assertTrue(u2_out_connection, "op_amp_out in op-amp1 should connect to U2 pin 5")
        
        # -------- Feedback Network Tests --------
        # Verify that the feedback network (R1-R2) is correctly connected in op-amp
        net_u1_minus = None
        for net_name, net_info in op_amp_nets.items():
            # Structure A: net_info is the list of nodes
            for node in net_info:
                if node["component"] == "U1" and node["pin"]["number"] == "2":
                    net_u1_minus = net_name
                    break
            if net_u1_minus:
                break
                
        self.assertIsNotNone(net_u1_minus, "Should find net for U1 inverting input")
        
        # Now check that R1 and R2 are connected to this net
        r1_connection = False
        r2_connection = False
        
        # Structure A: Access the list directly
        for node in op_amp_nets[net_u1_minus]:
            if node["component"] == "R1" and node["pin"]["number"] == "2":
                r1_connection = True
            elif node["component"] == "R2" and node["pin"]["number"] == "1":
                r2_connection = True
                
        self.assertTrue(r1_connection, "R1 should connect to U1 inverting input")
        self.assertTrue(r2_connection, "R2 should connect to U1 inverting input")
        
        # Verify that the feedback network (R3-R4) is correctly connected in op-amp1
        net_u2_minus = None
        for net_name, net_info in op_amp1_nets.items():
            # Structure A: net_info is the list of nodes
            for node in net_info:
                if node["component"] == "U2" and node["pin"]["number"] == "2":
                    net_u2_minus = net_name
                    break
            if net_u2_minus:
                break
                
        self.assertIsNotNone(net_u2_minus, "Should find net for U2 inverting input")
        
        # Now check that R3 and R4 are connected to this net
        r3_connection = False
        r4_connection = False
        
        # Structure A: Access the list directly
        for node in op_amp1_nets[net_u2_minus]:
            if node["component"] == "R3" and node["pin"]["number"] == "2":
                r3_connection = True
            elif node["component"] == "R4" and node["pin"]["number"] == "1":
                r4_connection = True
                
        self.assertTrue(r3_connection, "R3 should connect to U2 inverting input")
        self.assertTrue(r4_connection, "R4 should connect to U2 inverting input")
        
        # -------- Global Net Tests --------
        # Test that the global nets (+3V3, GND) in each subcircuit connect to the right components
        
        # Check GND connections in op-amp subcircuit
        gnd_connections_op_amp = {
            "C1_pin2": False,
            "R1_pin1": False,
            "U1_pin4": False
        }
        
        # Structure A: Access the list directly
        for node in op_amp_nets["GND"]:
            if node["component"] == "C1" and node["pin"]["number"] == "2":
                gnd_connections_op_amp["C1_pin2"] = True
            elif node["component"] == "R1" and node["pin"]["number"] == "1":
                gnd_connections_op_amp["R1_pin1"] = True
            elif node["component"] == "U1" and node["pin"]["number"] == "4":
                gnd_connections_op_amp["U1_pin4"] = True
                
        for conn, exists in gnd_connections_op_amp.items():
            self.assertTrue(exists, f"GND connection {conn} missing in op-amp subcircuit")
            
        # Check GND connections in op-amp1 subcircuit
        gnd_connections_op_amp1 = {
            "C2_pin2": False,
            "R3_pin1": False,
            "U2_pin4": False
        }
        
        # Structure A: Access the list directly
        for node in op_amp1_nets["GND"]:
            if node["component"] == "C2" and node["pin"]["number"] == "2":
                gnd_connections_op_amp1["C2_pin2"] = True
            elif node["component"] == "R3" and node["pin"]["number"] == "1":
                gnd_connections_op_amp1["R3_pin1"] = True
            elif node["component"] == "U2" and node["pin"]["number"] == "4":
                gnd_connections_op_amp1["U2_pin4"] = True
                
        for conn, exists in gnd_connections_op_amp1.items():
            self.assertTrue(exists, f"GND connection {conn} missing in op-amp1 subcircuit")
            
        # Check +3V3 connections in op-amp subcircuit (should connect to U1 pin 3)
        u1_power_connection = False
        # Structure A: Access the list directly
        for node in op_amp_nets["+3V3"]:
            if node["component"] == "U1" and node["pin"]["number"] == "3":
                u1_power_connection = True
                break
        self.assertTrue(u1_power_connection, "+3V3 should connect to U1 pin 3 in op-amp subcircuit")
        
        # Check +3V3 connections in op-amp1 subcircuit (should connect to U2 pin 3)
        u2_power_connection = False
        # Structure A: Access the list directly
        for node in op_amp1_nets["+3V3"]:
            if node["component"] == "U2" and node["pin"]["number"] == "3":
                u2_power_connection = True
                break
        self.assertTrue(u2_power_connection, "+3V3 should connect to U2 pin 3 in op-amp1 subcircuit")

        # -------- Property Tests --------
        self.assertIn("source", data["properties"], "Missing 'source' property")
        self.assertIn("date", data["properties"], "Missing 'date' property")
        self.assertIn("tool", data["properties"], "Missing 'tool' property")
        self.assertEqual(data["properties"]["tool"], "Eeschema 8.0.8", "Tool should be Eeschema 8.0.8")

        logger.info(f"Identical net names test => JSON output written to: {self.OUTPUT_JSON.resolve()}")


if __name__ == "__main__":
    unittest.main()