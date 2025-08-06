"""
Unit tests for the KiCad netlist importer, specifically focused on
verifying correct parsing of multiple top-level subcircuits in parallel.
"""

import json
import logging
import os
import unittest
from pathlib import Path

from circuit_synth.kicad.netlist_importer import convert_netlist

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestKicadParallelNetlistImporter(unittest.TestCase):
    """
    Tests the KiCad netlist importer against a complex netlist
    with multiple parallel subcircuits. Verifies hierarchy, components,
    nets, unconnected pins, and more.
    """

    @classmethod
    def setUpClass(cls):
        # Adjust the BASE_DIR relative to your project layout
        cls.BASE_DIR = Path(__file__).parent.parent

        # The test_data directory that holds netlist files
        cls.NETLIST_PATH = (
            cls.BASE_DIR / "test_data" / "kicad9" / "netlists" / "netlist5.net"
        )

        # Where we store the JSON output
        cls.OUTPUT_DIR = cls.BASE_DIR / "test_output"
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        cls.OUTPUT_JSON = cls.OUTPUT_DIR / "netlist5_output.json"

    def test_import_parallel_netlist(self):
        """
        Test that the netlist parallel.net is converted into the correct
        Circuit-Synth JSON. Verifies:
        1) File presence
        2) Top-level JSON structure
        3) Subcircuit hierarchy
        4) Components in each subcircuit
        5) Net distribution (including unconnected nets)
        6) Properties
        """

        # 1) Verify file presence
        self.assertTrue(
            self.NETLIST_PATH.is_file(),
            f"Missing test netlist file: {self.NETLIST_PATH}",
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

        # Circuit name should match the input file stem (e.g. "netlist_parallel")
        self.assertEqual(data["name"], self.NETLIST_PATH.stem)

        # -------- Top-Level Components Tests --------
        # Expect at least C1, U1 in the root
        self.assertIn(
            "C1", data["components"], "Root circuit should contain component C1"
        )
        self.assertIn(
            "U1", data["components"], "Root circuit should contain component U1"
        )

        c1 = data["components"]["C1"]
        self.assertEqual(c1["value"], "10uF", "C1 should have value 10uF")
        self.assertEqual(c1["footprint"], "Capacitor_SMD:C_0603_1608Metric")

        u1 = data["components"]["U1"]
        self.assertEqual(u1["value"], "ESP32-C6-MINI-1")
        self.assertEqual(u1["footprint"], "RF_Module:ESP32-C6-MINI-1")

        # -------- Subcircuit Hierarchy Tests --------
        # We expect multiple first-level subcircuits: /usb/, /power_filter/, /uSD_Card/
        # The "usb" subcircuit has a child "regulator" which has a child "led" which has child "light_sensor"

        subcircuits = data["subcircuits"]
        # Check for at least 3 top-level subcircuits
        self.assertGreaterEqual(
            len(subcircuits),
            3,
            "Expect at least 3 first-level subcircuits: usb, power_filter, uSD_Card",
        )

        # Find the specific subcircuits we know should exist
        def find_subcircuit(subckts, name):
            """Helper: Find a subcircuit by name"""
            for s in subckts:
                if s["name"] == name:
                    return s
            return None

        # Check for usb subcircuit and its hierarchy
        usb_subckt = find_subcircuit(subcircuits, "usb")
        self.assertIsNotNone(usb_subckt, "Should have 'usb' subcircuit at root level")
        self.assertIn(
            "P1", usb_subckt["components"], "USB subcircuit should contain P1"
        )
        self.assertIn(
            "R1", usb_subckt["components"], "USB subcircuit should contain R1"
        )

        # Check for power_filter subcircuit
        power_filter_subckt = find_subcircuit(subcircuits, "power_filter")
        self.assertIsNotNone(
            power_filter_subckt, "Should have 'power_filter' subcircuit at root level"
        )
        self.assertIn(
            "C4", power_filter_subckt["components"], "power_filter should contain C4"
        )
        self.assertIn(
            "C5", power_filter_subckt["components"], "power_filter should contain C5"
        )
        self.assertIn(
            "L1", power_filter_subckt["components"], "power_filter should contain L1"
        )

        # Check for uSD_Card subcircuit
        usd_subckt = find_subcircuit(subcircuits, "uSD_Card")
        self.assertIsNotNone(
            usd_subckt, "Should have 'uSD_Card' subcircuit at root level"
        )
        self.assertIn("C6", usd_subckt["components"], "uSD_Card should contain C6")
        self.assertIn("J1", usd_subckt["components"], "uSD_Card should contain J1")

        # Check that USB subcircuit has a regulator child
        usb_children = usb_subckt["subcircuits"]
        self.assertEqual(
            len(usb_children), 1, "USB should have 1 child subcircuit: 'regulator'"
        )
        regulator_subckt = usb_children[0]
        self.assertEqual(regulator_subckt["name"], "regulator")
        self.assertIn("C2", regulator_subckt["components"])
        self.assertIn("C3", regulator_subckt["components"])
        self.assertIn("U2", regulator_subckt["components"])

        # Check regulator -> led -> light_sensor hierarchy
        reg_children = regulator_subckt["subcircuits"]
        self.assertEqual(len(reg_children), 1, "Regulator should have 1 child: 'led'")

        led_subckt = reg_children[0]
        self.assertEqual(led_subckt["name"], "led")
        self.assertIn("D1", led_subckt["components"])
        self.assertIn("D2", led_subckt["components"])
        self.assertIn("R2", led_subckt["components"])
        self.assertIn("R3", led_subckt["components"])

        led_children = led_subckt["subcircuits"]
        self.assertEqual(
            len(led_children), 1, "LED should have 1 child: 'light_sensor'"
        )

        light_sensor_subckt = led_children[0]
        self.assertEqual(light_sensor_subckt["name"], "light_sensor")
        self.assertIn("U3", light_sensor_subckt["components"])

        # -------- Net Connectivity Tests --------
        # Check key nets in each subcircuit

        # Root level nets
        root_nets = data["nets"]
        self.assertIn("+3V3", root_nets, "Root nets should contain +3V3")
        self.assertIn("GND", root_nets, "Root nets should contain GND")

        # USB subcircuit nets - should contain +5V_USB but not +5V
        usb_nets = usb_subckt["nets"]
        self.assertIn("+5V_USB", usb_nets, "USB nets should contain +5V_USB")
        self.assertIn("GND", usb_nets, "USB nets should contain GND")

        # Verify +5V_USB in power_filter
        self.assertIn(
            "+5V_USB",
            power_filter_subckt["nets"],
            "Power filter should have +5V_USB net",
        )
        self.assertIn(
            "+5V", power_filter_subckt["nets"], "Power filter should have +5V net"
        )

        # Verify the inductor L1 is connecting +5V_USB to +5V in the power filter
        l1_usb_connected = False
        l1_5v_connected = False
        for net_name, net_info in power_filter_subckt["nets"].items():
            # Structure A: net_info is the list of nodes
            for node in net_info:
                if node["component"] == "L1":
                    if net_name == "+5V_USB" and node["pin"]["number"] == "1":
                        l1_usb_connected = True
                    elif net_name == "+5V" and node["pin"]["number"] == "2":
                        l1_5v_connected = True

        self.assertTrue(l1_usb_connected, "L1 pin 1 should connect to +5V_USB")
        self.assertTrue(l1_5v_connected, "L1 pin 2 should connect to +5V")

        # Verify the USB connector's VBUS pins are connected to +5V_USB and not +5V
        p1_vbus_connected = False
        for net_name, net_info in usb_nets.items():
            if net_name == "+5V_USB":
                # Structure A: net_info is the list of nodes
                for node in net_info:
                    if node["component"] == "P1" and node["pin"]["number"] in [
                        "A4",
                        "A9",
                        "B4",
                        "B9",
                    ]:
                        p1_vbus_connected = True
                        break
        self.assertTrue(
            p1_vbus_connected, "P1's VBUS pins should be connected to +5V_USB net"
        )

        # Check nets in regulator subcircuit
        regulator_nets = regulator_subckt["nets"]
        self.assertIn("+5V", regulator_nets, "Regulator nets should contain +5V")
        self.assertIn("+3V3", regulator_nets, "Regulator nets should contain +3V3")

        # Example check: confirm D1's anode connects to +5V in the 'led' subcircuit
        led_nets = led_subckt["nets"]
        d1_anode_net = None
        for net_name, net_info in led_nets.items():
            # Structure A: net_info is the list of nodes
            for node in net_info:
                if node["component"] == "D1" and node["pin"]["number"] == "2":
                    d1_anode_net = net_name
                    break
        self.assertEqual(
            d1_anode_net, "+5V", "D1 anode should be on +5V net in the LED subcircuit"
        )

        # -------- Unconnected Pin Tests --------
        # Check for unconnected pins in various subcircuits
        self.assertTrue(
            any(n.startswith("unconnected-(U1-") for n in root_nets),
            "Should have unconnected nets for U1 pins",
        )

        # -------- Properties Tests --------
        self.assertIn("source", data["properties"], "Missing 'source' property")
        self.assertIn("date", data["properties"], "Missing 'date' property")
        self.assertIn("tool", data["properties"], "Missing 'tool' property")
        self.assertIn("Eeschema", data["properties"]["tool"], "Tool should be Eeschema")

        logger.info(
            f"Parallel netlist => JSON output written to: {self.OUTPUT_JSON.resolve()}"
        )


if __name__ == "__main__":
    unittest.main()
