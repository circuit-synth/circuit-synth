import json
import os
import unittest
from pathlib import Path

from circuit_synth.kicad.netlist_importer import PinType, convert_netlist


class TestKicadHierarchicalNetlistImporter(unittest.TestCase):
    """
    Tests the KiCad netlist importer for netlist3.net which includes a hierarchical design
    with a parent-child sheet relationship.

    This is a comprehensive test to ensure proper handling of hierarchical circuits,
    global nets, component placement, and net connectivity across subcircuits.
    """

    @classmethod
    def setUpClass(cls):
        # Base directory: tests/ (i.e. three parents up from this file)
        cls.BASE_DIR = Path(__file__).parent.parent

        # Path to netlist3.net
        cls.NETLIST3_PATH = (
            cls.BASE_DIR / "test_data" / "kicad9" / "netlists" / "netlist3.net"
        )

        # Create output directory if it doesn't exist
        cls.OUTPUT_DIR = cls.BASE_DIR / "test_output"
        cls.OUTPUT_DIR.mkdir(exist_ok=True)

        # Output JSON path
        cls.OUTPUT3_JSON_PATH = cls.OUTPUT_DIR / "netlist3_output.json"

    def test_import_hierarchical_netlist(self):
        """
        Test parsing netlist3.net, verifying structure, components, nets, subcircuits, etc.
        This test ensures that:
        1. The hierarchical structure is properly maintained
        2. Components are placed in their correct subcircuits
        3. Nets are properly distributed across subcircuits based on connected components
        4. Global nets (power, ground) appear only in subcircuits where they have connections
        5. Component properties are preserved
        6. Pin types and connectivity are correctly represented
        """
        # 1) Verify file presence
        self.assertTrue(
            self.NETLIST3_PATH.is_file(),
            f"Missing test netlist file: {self.NETLIST3_PATH}",
        )

        # 2) Convert netlist3.net => netlist3_output.json
        convert_netlist(self.NETLIST3_PATH, self.OUTPUT3_JSON_PATH)
        self.assertTrue(self.OUTPUT3_JSON_PATH.exists())

        # 3) Load the JSON and check structure
        with self.OUTPUT3_JSON_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # -------- Basic Structure Tests --------
        # Check all required top-level fields exist
        required_fields = ["name", "components", "nets", "subcircuits", "properties"]
        for field in required_fields:
            self.assertIn(field, data, f"Missing required top-level field: {field}")

        # Circuit name should match input file name
        self.assertEqual(
            data["name"], "netlist3", "Circuit name should match input file name"
        )

        # -------- Hierarchical Structure Tests --------
        # Verify there's exactly one subcircuit named "usb"
        self.assertEqual(
            len(data["subcircuits"]), 1, "Should have exactly one subcircuit"
        )
        usb_subcircuit = data["subcircuits"][0]
        self.assertEqual(
            usb_subcircuit["name"], "usb", "Subcircuit should be named 'usb'"
        )

        # Verify subcircuit has correct structure
        subcircuit_fields = ["name", "components", "nets", "subcircuits"]
        for field in subcircuit_fields:
            self.assertIn(
                field, usb_subcircuit, f"Missing required subcircuit field: {field}"
            )

        # Verify USB subcircuit doesn't have nested subcircuits (leaf node)
        self.assertEqual(
            len(usb_subcircuit["subcircuits"]),
            0,
            "USB subcircuit should not have any child subcircuits",
        )

        # -------- Component Placement Tests --------
        # Root level should have exactly U1
        self.assertEqual(
            len(data["components"]), 1, "Root circuit should have exactly one component"
        )
        self.assertIn(
            "U1", data["components"], "Root circuit should contain component U1"
        )

        # U1 should be ESP32-C6-MINI-1
        u1 = data["components"]["U1"]
        self.assertEqual(
            u1["value"], "ESP32-C6-MINI-1", "U1 should be an ESP32-C6-MINI-1"
        )
        self.assertEqual(
            u1["footprint"],
            "RF_Module:ESP32-C6-MINI-1",
            "U1 should have correct footprint",
        )

        # USB subcircuit should have exactly P1 and R2
        usb_components = usb_subcircuit["components"]
        self.assertEqual(
            len(usb_components), 2, "USB subcircuit should have exactly two components"
        )
        self.assertIn("P1", usb_components, "USB subcircuit should contain P1")
        self.assertIn("R2", usb_components, "USB subcircuit should contain R2")

        # Verify P1 properties
        p1 = usb_components["P1"]
        self.assertEqual(
            p1["value"], "USB_C_Plug_USB2.0", "P1 should be a USB_C_Plug_USB2.0"
        )
        self.assertEqual(
            p1["description"],
            "USB 2.0-only Type-C Plug connector",
            "P1 should have correct description",
        )

        # Verify R2 properties
        r2 = usb_components["R2"]
        self.assertEqual(r2["value"], "10k", "R2 should be a 10k resistor")
        self.assertEqual(
            r2["footprint"],
            "Resistor_SMD:R_0603_1608Metric",
            "R2 should have correct footprint",
        )

        # -------- Net Distribution Tests --------
        # Check root circuit nets
        root_nets = data["nets"]
        expected_root_nets = [
            "+3V3",
            "D+",
            "D-",
            "GND",
        ]  # These are the nets connected to U1
        for net_name in expected_root_nets:
            self.assertIn(
                net_name, root_nets, f"Root circuit should contain net {net_name}"
            )

        # +5V should NOT be in root circuit (no connections there)
        self.assertNotIn(
            "+5V", root_nets, "+5V should not appear in root circuit (no connections)"
        )

        # Check USB subcircuit nets
        usb_nets = usb_subcircuit["nets"]
        expected_usb_nets = [
            "+5V",
            "D+",
            "D-",
            "GND",
            "Net-(P1-CC)",
            "unconnected-(P1-VCONN-PadB5)",
        ]
        for net_name in expected_usb_nets:
            self.assertIn(
                net_name, usb_nets, f"USB subcircuit should contain net {net_name}"
            )

        # +3V3 should NOT be in USB subcircuit (no connections there)
        self.assertNotIn(
            "+3V3",
            usb_nets,
            "+3V3 should not appear in USB subcircuit (no connections)",
        )

        # -------- Net Connectivity Tests --------
        # Test +3V3 net - should only connect to U1 pin 3
        plus3v3_nodes = root_nets["+3V3"]  # Structure A
        self.assertEqual(
            len(plus3v3_nodes), 1, "+3V3 should connect to exactly one pin"
        )
        self.assertEqual(
            plus3v3_nodes[0]["component"], "U1", "+3V3 should connect to U1"
        )
        self.assertEqual(
            plus3v3_nodes[0]["pin"]["number"], "3", "+3V3 should connect to U1 pin 3"
        )
        self.assertEqual(
            plus3v3_nodes[0]["pin"]["name"], "3V3", "+3V3 should connect to U1.3V3"
        )
        self.assertEqual(
            plus3v3_nodes[0]["pin"]["type"],
            "power_in",
            "+3V3 pin should be power_in type",
        )

        # Test D+ net in root - should connect to U1.IO20
        dplus_root_nodes = root_nets["D+"]  # Structure A
        self.assertEqual(
            len(dplus_root_nodes), 1, "D+ in root should connect to exactly one pin"
        )
        self.assertEqual(
            dplus_root_nodes[0]["component"], "U1", "D+ in root should connect to U1"
        )
        self.assertEqual(
            dplus_root_nodes[0]["pin"]["number"],
            "26",
            "D+ in root should connect to U1 pin 26",
        )
        self.assertEqual(
            dplus_root_nodes[0]["pin"]["name"],
            "IO20",
            "D+ in root should connect to U1.IO20",
        )

        # Test D+ net in USB subcircuit - should connect to P1.A6
        dplus_usb_nodes = usb_nets["D+"]  # Structure A
        self.assertEqual(
            len(dplus_usb_nodes), 1, "D+ in USB should connect to exactly one pin"
        )
        self.assertEqual(
            dplus_usb_nodes[0]["component"], "P1", "D+ in USB should connect to P1"
        )
        self.assertEqual(
            dplus_usb_nodes[0]["pin"]["number"],
            "A6",
            "D+ in USB should connect to P1 pin A6",
        )
        self.assertEqual(
            dplus_usb_nodes[0]["pin"]["name"], "D+", "D+ in USB should connect to P1.D+"
        )

        # -------- Global Nets Tests --------
        # Test GND net in root circuit - should connect to all U1 GND pins
        gnd_root_nodes = root_nets["GND"]  # Structure A
        u1_gnd_pins = ["1", "2", "11", "14"]  # First 4 GND pins of U1
        for pin_num in u1_gnd_pins:
            pin_found = False
            for node in gnd_root_nodes:
                if node["component"] == "U1" and node["pin"]["number"] == pin_num:
                    pin_found = True
                    break
            self.assertTrue(
                pin_found, f"GND in root should connect to U1 pin {pin_num}"
            )

        # Test GND net in USB subcircuit - should connect to P1 grounds and R2
        gnd_usb_nodes = usb_nets["GND"]  # Structure A
        p1_gnd_pins = ["A1", "A12", "B1", "B12", "S1"]  # All P1 ground pins
        for pin_num in p1_gnd_pins:
            pin_found = False
            for node in gnd_usb_nodes:
                if node["component"] == "P1" and node["pin"]["number"] == pin_num:
                    pin_found = True
                    break
            self.assertTrue(pin_found, f"GND in USB should connect to P1 pin {pin_num}")

        # Verify R2 pin 2 connects to GND
        r2_pin2_found = False
        for node in gnd_usb_nodes:  # Already a list
            if node["component"] == "R2" and node["pin"]["number"] == "2":
                r2_pin2_found = True
                break
        self.assertTrue(r2_pin2_found, "GND in USB should connect to R2 pin 2")

        # -------- Special Net Tests --------
        # Test Net-(P1-CC) - should connect P1.A5 to R2.1
        cc_nodes = usb_nets["Net-(P1-CC)"]  # Structure A: cc_nodes is the list
        self.assertEqual(
            len(cc_nodes), 2, "Net-(P1-CC) should have exactly 2 connections"
        )

        p1_cc_found = False
        r2_pin1_found = False
        for node in cc_nodes:  # Already a list
            if node["component"] == "P1" and node["pin"]["number"] == "A5":
                p1_cc_found = True
            if node["component"] == "R2" and node["pin"]["number"] == "1":
                r2_pin1_found = True

        self.assertTrue(p1_cc_found, "Net-(P1-CC) should connect to P1.A5")
        self.assertTrue(r2_pin1_found, "Net-(P1-CC) should connect to R2.1")

        # Test +5V net in USB - should connect to all 4 VBUS pins
        vbus_nodes = usb_nets["+5V"]  # Structure A: vbus_nodes is the list
        vbus_pin_count = 0
        for node in vbus_nodes:  # Already a list
            if node["component"] == "P1" and node["pin"]["name"] == "VBUS":
                vbus_pin_count += 1

        self.assertEqual(vbus_pin_count, 4, "+5V should connect to all 4 VBUS pins")

        # -------- Unconnected Pin Tests --------
        # Verify unconnected pins of U1 are correctly represented
        unconnected_io_pins = [
            "IO0",
            "IO1",
            "IO2",
            "IO3",
            "IO4",
            "IO5",
            "IO6",
            "IO7",
            "IO8",
            "IO9",
            "IO12",
            "IO13",
            "IO14",
            "IO15",
            "IO18",
            "IO21",
            "IO22",
            "IO23",
        ]

        for io_name in unconnected_io_pins:
            net_name = f"unconnected-(U1-{io_name}-Pad"
            found = False
            for net in root_nets:
                if net.startswith(net_name):
                    found = True
                    break
            self.assertTrue(found, f"Missing unconnected net for U1.{io_name}")

        # Verify unconnected P1.VCONN pin
        self.assertIn(
            "unconnected-(P1-VCONN-PadB5)",
            usb_nets,
            "Missing unconnected net for P1.VCONN",
        )

        # -------- Properties Tests --------
        # Check top-level properties
        self.assertIn("source", data["properties"], "Missing source property")
        self.assertIn("date", data["properties"], "Missing date property")
        self.assertIn("tool", data["properties"], "Missing tool property")
        self.assertEqual(
            data["properties"]["tool"], "Eeschema 8.0.8", "Incorrect tool version"
        )

        print(
            f"netlist3.net => JSON output written to: {self.OUTPUT3_JSON_PATH.resolve()}"
        )

    def test_import_netlist4(self):
        """
        Test parsing netlist4.net, verifying structure, components, nets, and deep hierarchical relationships.
        This netlist contains a complex hierarchy with multiple levels:
        - Root level with ESP32 and capacitor
        - USB connection sheet
        - Voltage regulator subsystem
        - LED indicators
        - Light sensor at the deepest level
        """
        # Path to netlist4.net
        NETLIST4_PATH = (
            self.BASE_DIR / "test_data" / "kicad9" / "netlists" / "netlist4.net"
        )

        # Output JSON path
        OUTPUT4_JSON_PATH = self.OUTPUT_DIR / "netlist4_output.json"

        # 1) Verify file presence
        self.assertTrue(
            NETLIST4_PATH.is_file(), f"Missing test netlist file: {NETLIST4_PATH}"
        )

        # 2) Convert netlist4.net => netlist4_output.json
        convert_netlist(NETLIST4_PATH, OUTPUT4_JSON_PATH)
        self.assertTrue(OUTPUT4_JSON_PATH.exists())

        # 3) Load the JSON and check structure
        with OUTPUT4_JSON_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # -------- Basic Structure Tests --------
        # Check all required top-level fields exist
        required_fields = ["name", "components", "nets", "subcircuits", "properties"]
        for field in required_fields:
            self.assertIn(field, data, f"Missing required top-level field: {field}")

        # Circuit name should match input file name
        self.assertEqual(
            data["name"], "netlist4", "Circuit name should match input file name"
        )

        # -------- Root Level Component Tests --------
        # Root level should have C1 and U1
        self.assertEqual(
            len(data["components"]),
            2,
            "Root circuit should have exactly two components",
        )
        self.assertIn(
            "C1", data["components"], "Root circuit should contain component C1"
        )
        self.assertIn(
            "U1", data["components"], "Root circuit should contain component U1"
        )

        # Verify C1 properties
        c1 = data["components"]["C1"]
        self.assertEqual(c1["value"], "10uF", "C1 should be a 10uF capacitor")
        self.assertEqual(
            c1["footprint"],
            "Capacitor_SMD:C_0603_1608Metric",
            "C1 should have correct footprint",
        )

        # U1 should be ESP32-C6-MINI-1
        u1 = data["components"]["U1"]
        self.assertEqual(
            u1["value"], "ESP32-C6-MINI-1", "U1 should be an ESP32-C6-MINI-1"
        )
        self.assertEqual(
            u1["footprint"],
            "RF_Module:ESP32-C6-MINI-1",
            "U1 should have correct footprint",
        )

        # -------- First-Level Hierarchy (USB) Tests --------
        # Should have exactly one subcircuit at root level
        self.assertEqual(
            len(data["subcircuits"]),
            1,
            "Should have exactly one first-level subcircuit",
        )
        usb_subcircuit = data["subcircuits"][0]
        self.assertEqual(
            usb_subcircuit["name"], "usb", "First subcircuit should be named 'usb'"
        )

        # Verify USB subcircuit components
        usb_components = usb_subcircuit["components"]
        self.assertEqual(
            len(usb_components), 2, "USB subcircuit should have exactly two components"
        )
        self.assertIn("P1", usb_components, "USB subcircuit should contain P1")
        self.assertIn("R1", usb_components, "USB subcircuit should contain R1")

        # Verify P1 properties
        p1 = usb_components["P1"]
        self.assertEqual(
            p1["value"], "USB_C_Plug_USB2.0", "P1 should be a USB_C_Plug_USB2.0"
        )

        # Verify R1 properties
        r1 = usb_components["R1"]
        self.assertEqual(r1["value"], "10k", "R1 should be a 10k resistor")

        # -------- Second-Level Hierarchy (Regulator) Tests --------
        # USB should have exactly one subcircuit (regulator)
        self.assertEqual(
            len(usb_subcircuit["subcircuits"]),
            1,
            "USB should have exactly one subcircuit",
        )
        regulator = usb_subcircuit["subcircuits"][0]
        self.assertEqual(
            regulator["name"],
            "regulator",
            "Second-level subcircuit should be named 'regulator'",
        )

        # Verify regulator components
        reg_components = regulator["components"]
        self.assertEqual(
            len(reg_components),
            3,
            "Regulator subcircuit should have exactly three components",
        )
        self.assertIn("C2", reg_components, "Regulator should contain C2")
        self.assertIn("C3", reg_components, "Regulator should contain C3")
        self.assertIn("U2", reg_components, "Regulator should contain U2")

        # Verify U2 properties
        u2 = reg_components["U2"]
        self.assertEqual(
            u2["value"], "AMS1117-3.3", "U2 should be an AMS1117-3.3 regulator"
        )
        self.assertEqual(
            u2["footprint"],
            "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
            "U2 should have correct footprint",
        )

        # -------- Third-Level Hierarchy (LED) Tests --------
        # Regulator should have exactly one subcircuit (LED)
        self.assertEqual(
            len(regulator["subcircuits"]),
            1,
            "Regulator should have exactly one subcircuit",
        )
        led = regulator["subcircuits"][0]
        self.assertEqual(
            led["name"], "led", "Third-level subcircuit should be named 'led'"
        )

        # Verify LED components
        led_components = led["components"]
        self.assertEqual(
            len(led_components), 4, "LED subcircuit should have exactly four components"
        )
        self.assertIn("D1", led_components, "LED subcircuit should contain D1")
        self.assertIn("D2", led_components, "LED subcircuit should contain D2")
        self.assertIn("R2", led_components, "LED subcircuit should contain R2")
        self.assertIn("R3", led_components, "LED subcircuit should contain R3")

        # Verify D1 and D2 are LEDs
        self.assertEqual(led_components["D1"]["value"], "LED", "D1 should be an LED")
        self.assertEqual(led_components["D2"]["value"], "LED", "D2 should be an LED")

        # Verify resistor values
        self.assertEqual(
            led_components["R2"]["value"], "330r", "R2 should be a 330 ohm resistor"
        )
        self.assertEqual(
            led_components["R3"]["value"], "220r", "R3 should be a 220 ohm resistor"
        )

        # -------- Fourth-Level Hierarchy (Light Sensor) Tests --------
        # LED should have exactly one subcircuit (light_sensor)
        self.assertEqual(
            len(led["subcircuits"]), 1, "LED should have exactly one subcircuit"
        )
        light_sensor = led["subcircuits"][0]
        self.assertEqual(
            light_sensor["name"],
            "light_sensor",
            "Fourth-level subcircuit should be named 'light_sensor'",
        )

        # Verify light sensor components
        sensor_components = light_sensor["components"]
        self.assertEqual(
            len(sensor_components),
            1,
            "Light sensor subcircuit should have exactly one component",
        )
        self.assertIn(
            "U3", sensor_components, "Light sensor subcircuit should contain U3"
        )

        # Verify U3 properties
        u3 = sensor_components["U3"]
        self.assertEqual(
            u3["value"], "APDS-9301", "U3 should be an APDS-9301 light sensor"
        )
        self.assertEqual(
            u3["footprint"],
            "OptoDevice:Broadcom_APDS-9301",
            "U3 should have correct footprint",
        )

        # -------- Net Connectivity Tests --------
        # Test major nets at root level
        root_nets = data["nets"]

        # +3V3 net should connect components across multiple sheets
        self.assertIn("+3V3", root_nets, "Root circuit should contain +3V3 net")
        plus3v3_nodes = root_nets["+3V3"]  # Structure A

        # Find components connected to +3V3
        plus3v3_connections = []
        for node in plus3v3_nodes:  # Already a list
            plus3v3_connections.append(f"{node['component']}.{node['pin']['number']}")

        # C1 and U1 should be connected to +3V3 in root circuit
        self.assertIn("C1.1", plus3v3_connections, "+3V3 should connect to C1 pin 1")
        self.assertIn("U1.3", plus3v3_connections, "+3V3 should connect to U1 pin 3")

        # Test GND net in root circuit
        self.assertIn("GND", root_nets, "Root circuit should contain GND net")
        gnd_nodes = root_nets["GND"]  # Structure A

        # Find components connected to GND
        gnd_connections = []
        for node in gnd_nodes:  # Already a list
            gnd_connections.append(f"{node['component']}.{node['pin']['number']}")

        # C1 and multiple U1 pins should be connected to GND
        self.assertIn("C1.2", gnd_connections, "GND should connect to C1 pin 2")
        self.assertIn("U1.1", gnd_connections, "GND should connect to U1 pin 1")
        self.assertIn("U1.2", gnd_connections, "GND should connect to U1 pin 2")

        # Check USB interface connections (D+/D-)
        self.assertIn("D+", root_nets, "Root circuit should contain D+ net")
        self.assertIn("D-", root_nets, "Root circuit should contain D- net")

        dplus_nodes = root_nets["D+"]  # Structure A
        dminus_nodes = root_nets["D-"]  # Structure A

        # Find which U1 pin connects to D+
        u1_dplus_pin = None
        for node in dplus_nodes:  # Already a list
            if node["component"] == "U1":
                u1_dplus_pin = node["pin"]["number"]
                break

        self.assertEqual(u1_dplus_pin, "26", "D+ should connect to U1 pin 26 (IO20)")

        # Find which U1 pin connects to D-
        u1_dminus_pin = None
        for node in dminus_nodes:  # Already a list
            if node["component"] == "U1":
                u1_dminus_pin = node["pin"]["number"]
                break

        self.assertEqual(u1_dminus_pin, "25", "D- should connect to U1 pin 25 (IO19)")

        # Check I2C connections for light sensor
        self.assertIn("SCL", root_nets, "Root circuit should contain SCL net")
        self.assertIn("SDA", root_nets, "Root circuit should contain SDA net")

        # Find which U1 pins connect to SCL/SDA
        u1_scl_pin = None
        u1_sda_pin = None

        for node in root_nets["SCL"]:  # Structure A
            if node["component"] == "U1":
                u1_scl_pin = node["pin"]["number"]

        for node in root_nets["SDA"]:  # Structure A
            if node["component"] == "U1":
                u1_sda_pin = node["pin"]["number"]

        self.assertEqual(u1_scl_pin, "18", "SCL should connect to U1 pin 18 (IO13)")
        self.assertEqual(u1_sda_pin, "17", "SDA should connect to U1 pin 17 (IO12)")

        # Check interrupt connection
        self.assertIn("INT", root_nets, "Root circuit should contain INT net")
        u1_int_pin = None

        for node in root_nets["INT"]:  # Structure A
            if node["component"] == "U1":
                u1_int_pin = node["pin"]["number"]

        self.assertEqual(u1_int_pin, "19", "INT should connect to U1 pin 19 (IO14)")

        # -------- USB Subcircuit Net Tests --------
        usb_nets = usb_subcircuit["nets"]

        # Check USB CC connection to pull-down resistor
        self.assertIn("Net-(P1-CC)", usb_nets, "USB subcircuit should contain CC net")
        cc_nodes = usb_nets["Net-(P1-CC)"]  # Structure A

        # Find connections for CC net
        cc_connections = []
        for node in cc_nodes:  # Already a list
            cc_connections.append(f"{node['component']}.{node['pin']['number']}")

        self.assertIn("P1.A5", cc_connections, "CC net should connect to P1 pin A5")
        self.assertIn("R1.1", cc_connections, "CC net should connect to R1 pin 1")

        # Verify R1 pin 2 goes to GND
        r1_pin2_connection = None
        for net_name, net_nodes in usb_nets.items():  # Use net_nodes for clarity
            # Structure A: net_nodes is the list of nodes
            for node in net_nodes:
                if node["component"] == "R1" and node["pin"]["number"] == "2":
                    r1_pin2_connection = net_name
                    break

        self.assertEqual(r1_pin2_connection, "GND", "R1 pin 2 should connect to GND")

        # -------- Regulator Subcircuit Net Tests --------
        reg_nets = regulator["nets"]

        # Check regulator input and output connections
        # Input should be +5V, output should be +3V3

        # Find U2 pin connections
        u2_pins = {}
        for net_name, net_nodes in reg_nets.items():  # Use net_nodes for clarity
            # Structure A: net_nodes is the list of nodes
            for node in net_nodes:
                if node["component"] == "U2":
                    u2_pins[node["pin"]["number"]] = net_name

        self.assertEqual(
            u2_pins.get("1"), "GND", "U2 pin 1 (GND) should connect to GND"
        )
        self.assertEqual(
            u2_pins.get("2"), "+3V3", "U2 pin 2 (VO) should connect to +3V3"
        )
        self.assertEqual(u2_pins.get("3"), "+5V", "U2 pin 3 (VI) should connect to +5V")

        # Verify capacitor connections
        # C2 should be between +5V and GND
        # C3 should be between +3V3 and GND

        c2_pins = {}
        c3_pins = {}

        for net_name, net_nodes in reg_nets.items():  # Use net_nodes for clarity
            # Structure A: net_nodes is the list of nodes
            for node in net_nodes:
                if node["component"] == "C2":
                    c2_pins[node["pin"]["number"]] = net_name
                elif node["component"] == "C3":
                    c3_pins[node["pin"]["number"]] = net_name

        self.assertEqual(c2_pins.get("1"), "+5V", "C2 pin 1 should connect to +5V")
        self.assertEqual(c2_pins.get("2"), "GND", "C2 pin 2 should connect to GND")
        self.assertEqual(c3_pins.get("1"), "+3V3", "C3 pin 1 should connect to +3V3")
        self.assertEqual(c3_pins.get("2"), "GND", "C3 pin 2 should connect to GND")

        # -------- LED Subcircuit Net Tests --------
        led_nets = led["nets"]

        # D1 should be connected to +5V through R2
        # D2 should be connected to +3V3 through R3

        # Find LED connections
        d1_pins = {}
        d2_pins = {}
        r2_pins = {}
        r3_pins = {}

        for net_name, net_nodes in led_nets.items():  # Use net_nodes for clarity
            # Structure A: net_nodes is the list of nodes
            for node in net_nodes:
                if node["component"] == "D1":
                    d1_pins[node["pin"]["number"]] = net_name
                elif node["component"] == "D2":
                    d2_pins[node["pin"]["number"]] = net_name
                elif node["component"] == "R2":
                    r2_pins[node["pin"]["number"]] = net_name
                elif node["component"] == "R3":
                    r3_pins[node["pin"]["number"]] = net_name

        # Check D1 (5V indicator)
        self.assertEqual(d1_pins.get("2"), "+5V", "D1 anode should connect to +5V")
        self.assertEqual(
            d1_pins.get("1"),
            "Net-(D1-K)",
            "D1 cathode should connect to current limiting resistor",
        )
        self.assertEqual(
            r2_pins.get("1"), "Net-(D1-K)", "R2 should connect to D1 cathode"
        )
        self.assertEqual(r2_pins.get("2"), "GND", "R2 should connect to GND")

        # Check D2 (3.3V indicator)
        self.assertEqual(d2_pins.get("2"), "+3V3", "D2 anode should connect to +3V3")
        self.assertEqual(
            d2_pins.get("1"),
            "Net-(D2-K)",
            "D2 cathode should connect to current limiting resistor",
        )
        self.assertEqual(
            r3_pins.get("1"), "Net-(D2-K)", "R3 should connect to D2 cathode"
        )
        self.assertEqual(r3_pins.get("2"), "GND", "R3 should connect to GND")

        # -------- Light Sensor Subcircuit Net Tests --------
        sensor_nets = light_sensor["nets"]

        # Find light sensor connections
        u3_pins = {}

        for net_name, net_nodes in sensor_nets.items():  # Use net_nodes for clarity
            # Structure A: net_nodes is the list of nodes
            for node in net_nodes:
                if node["component"] == "U3":
                    u3_pins[node["pin"]["number"]] = net_name

        # Check power connections
        self.assertEqual(
            u3_pins.get("1"), "+3V3", "U3 pin 1 (VDD) should connect to +3V3"
        )
        self.assertEqual(
            u3_pins.get("2"), "GND", "U3 pin 2 (GND) should connect to GND"
        )

        # Check I2C and interrupt connections
        self.assertEqual(u3_pins.get("4"), "SCL", "U3 pin 4 should connect to SCL")
        self.assertEqual(u3_pins.get("5"), "SDA", "U3 pin 5 should connect to SDA")
        self.assertEqual(u3_pins.get("6"), "INT", "U3 pin 6 should connect to INT")

        # Check address select pin (connected to GND)
        self.assertEqual(
            u3_pins.get("3"), "GND", "U3 pin 3 (ADR_SEL) should connect to GND"
        )

        # -------- Unconnected Pin Tests --------
        # Verify some unconnected pins of U1 are correctly represented
        unconnected_io_pins = [
            "IO0",
            "IO1",
            "IO2",
            "IO3",
            "IO4",
            "IO5",
            "IO6",
            "IO7",
            "IO8",
            "IO9",
            "IO15",
            "IO18",
            "IO21",
            "IO22",
            "IO23",
        ]

        for io_name in unconnected_io_pins:
            net_name = f"unconnected-(U1-{io_name}-Pad"
            found = False
            for net in root_nets:
                if net.startswith(net_name):
                    found = True
                    break
            self.assertTrue(found, f"Missing unconnected net for U1.{io_name}")

        # Verify unconnected P1.VCONN pin
        vconn_found = False
        for net in usb_nets:
            if net.startswith("unconnected-(P1-VCONN-"):
                vconn_found = True
                break
        self.assertTrue(vconn_found, "Missing unconnected net for P1.VCONN")

        # -------- Properties Tests --------
        # Check top-level properties
        self.assertIn("source", data["properties"], "Missing source property")
        self.assertIn("date", data["properties"], "Missing date property")
        self.assertIn("tool", data["properties"], "Missing tool property")
        self.assertEqual(
            data["properties"]["tool"], "Eeschema 8.0.8", "Incorrect tool version"
        )

        print(f"netlist4.net => JSON output written to: {OUTPUT4_JSON_PATH.resolve()}")


if __name__ == "__main__":
    unittest.main()
