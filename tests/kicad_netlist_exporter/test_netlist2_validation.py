import json
import re
from pathlib import Path

from .test_netlist_validation_base import NetlistValidationBase


class TestNetlist2Validation(NetlistValidationBase):
    """
    Thorough test for validating that netlist2_output.json correctly represents
    the original netlist2.net file.

    Tests proper handling of different pin types, including:
    - power_in, power_out, input, output, bidirectional, passive, no_connect
    - Components including microcontroller, LEDs, resistors, and unconnected pins
    """

    @classmethod
    def setUpClass(cls):
        # Base directory: tests/ (i.e. three parents up from this file)
        cls.BASE_DIR = Path(__file__).parent.parent

        # Test data and output directories
        cls.TEST_DATA_DIR = cls.BASE_DIR / "test_data" / "kicad9" / "netlists"
        cls.TEST_OUTPUT_DIR = cls.BASE_DIR / "test_output"

        # Specific files for this test
        cls.NETLIST_FILE = cls.TEST_DATA_DIR / "netlist2.net"
        cls.JSON_FILE = cls.TEST_OUTPUT_DIR / "netlist2_output.json"
        cls.EXPORTED_NETLIST_FILE = cls.TEST_OUTPUT_DIR / "netlist2_exported.net"

        # Load the files
        cls.netlist_content = cls.NETLIST_FILE.read_text(encoding="utf-8")
        with open(cls.JSON_FILE, "r", encoding="utf-8") as f:
            cls.json_data = json.load(f)

        # Ensure files exist
        assert cls.NETLIST_FILE.exists(), f"Netlist file not found: {cls.NETLIST_FILE}"
        assert cls.JSON_FILE.exists(), f"JSON file not found: {cls.JSON_FILE}"

    def test_file_existence(self):
        """Test that both the netlist and JSON files exist."""
        self.assertTrue(
            self.NETLIST_FILE.exists(), f"Netlist file not found: {self.NETLIST_FILE}"
        )
        self.assertTrue(
            self.JSON_FILE.exists(), f"JSON file not found: {self.JSON_FILE}"
        )

    def test_basic_properties(self):
        """Test that basic properties are correctly extracted."""
        # Check name
        self.assertEqual(self.json_data["name"], "netlist2", "Incorrect netlist name")

        # Check properties
        self.assertIn("properties", self.json_data, "Missing properties section")
        self.assertIn("source", self.json_data["properties"], "Missing source property")
        self.assertIn("date", self.json_data["properties"], "Missing date property")
        self.assertIn("tool", self.json_data["properties"], "Missing tool property")

        # Extract properties from netlist with more flexible patterns
        source_match = re.search(r'\(source\s+"([^"]+)"\)', self.netlist_content)
        date_match = re.search(r'\(date\s+"([^"]+)"\)', self.netlist_content)
        tool_match = re.search(r'\(tool\s+"([^"]+)"\)', self.netlist_content)

        # Verify properties match if found
        if source_match:
            self.assertEqual(
                self.json_data["properties"]["source"],
                source_match.group(1),
                "Source property mismatch",
            )
        if date_match:
            self.assertEqual(
                self.json_data["properties"]["date"],
                date_match.group(1),
                "Date property mismatch",
            )
        if tool_match:
            self.assertEqual(
                self.json_data["properties"]["tool"],
                tool_match.group(1),
                "Tool property mismatch",
            )

    def test_component_count(self):
        """Test that all components are correctly extracted."""
        # Extract components from netlist with more flexible pattern
        netlist_components = re.findall(
            r'\(comp\s+\(ref\s+"([^"]+)"\)', self.netlist_content
        )

        # Count components in JSON
        json_components = list(self.json_data["components"].keys())

        # Verify component counts match
        self.assertEqual(
            len(json_components),
            len(netlist_components),
            f"Component count mismatch: {len(json_components)} in JSON vs {len(netlist_components)} in netlist",
        )

        # Verify all components from netlist are in JSON
        for comp_ref in netlist_components:
            self.assertIn(
                comp_ref, json_components, f"Component {comp_ref} missing from JSON"
            )

        # Verify key components
        key_components = ["D1", "R1", "U1"]
        for comp_ref in key_components:
            self.assertIn(
                comp_ref, json_components, f"Key component {comp_ref} missing from JSON"
            )

    def test_component_properties(self):
        """Test that component properties are correctly extracted."""
        # Test D1 component properties
        self.assert_component_property(
            self.json_data["components"], "D1", "reference", "D1"
        )
        self.assert_component_property(
            self.json_data["components"], "D1", "value", "LED"
        )
        self.assert_component_property(
            self.json_data["components"],
            "D1",
            "footprint",
            "LED_SMD:LED_0603_1608Metric",
        )

        # Test R1 component properties
        self.assert_component_property(
            self.json_data["components"], "R1", "reference", "R1"
        )
        self.assert_component_property(
            self.json_data["components"], "R1", "value", "10k"
        )
        self.assert_component_property(
            self.json_data["components"],
            "R1",
            "footprint",
            "Resistor_SMD:R_0603_1608Metric",
        )

        # Test U1 component properties
        self.assert_component_property(
            self.json_data["components"], "U1", "reference", "U1"
        )
        self.assert_component_property(
            self.json_data["components"], "U1", "value", "ESP32-C6-MINI-1"
        )
        self.assert_component_property(
            self.json_data["components"], "U1", "footprint", "RF_Module:ESP32-C6-MINI-1"
        )

    def test_net_count(self):
        """Test that all nets are correctly extracted."""
        # Extract nets from netlist with more flexible pattern
        netlist_nets = re.findall(
            r'\(net\s+\(code\s+"[^"]+"\)\s+\(name\s+"([^"]+)"\)', self.netlist_content
        )

        # Count nets in JSON
        json_nets = list(self.json_data["nets"].keys())

        # Verify net counts match
        self.assertEqual(
            len(json_nets),
            len(netlist_nets),
            f"Net count mismatch: {len(json_nets)} in JSON vs {len(netlist_nets)} in netlist",
        )

        # Verify all nets from netlist are in JSON
        for net_name in netlist_nets:
            self.assertIn(net_name, json_nets, f"Net {net_name} missing from JSON")

        # Verify key nets
        key_nets = ["+3V3", "GND", "Net-(D1-A)"]
        for net_name in key_nets:
            self.assertIn(net_name, json_nets, f"Key net {net_name} missing from JSON")

    def test_net_nodes(self):
        """Test that net nodes are correctly extracted."""
        # Check +3V3 net nodes
        self.assertIn("+3V3", self.json_data["nets"], "+3V3 net missing from JSON")
        v3v3_net = self.json_data["nets"]["+3V3"]

        # Check that +3V3 net has nodes (v3v3_net is the list of nodes in Structure A)
        self.assertIsInstance(
            v3v3_net, list, "+3V3 net data should be a list (Structure A)"
        )
        self.assertGreater(len(v3v3_net), 0, "+3V3 net has no nodes in JSON")

        # Check specific node connections (pass the list of nodes)
        self.check_net_nodes(v3v3_net, "U1")

        # Check GND net nodes
        self.assertIn("GND", self.json_data["nets"], "GND net missing from JSON")
        gnd_net = self.json_data["nets"]["GND"]

        # Check that GND net has nodes (gnd_net is the list of nodes in Structure A)
        self.assertIsInstance(
            gnd_net, list, "GND net data should be a list (Structure A)"
        )
        self.assertGreater(len(gnd_net), 0, "GND net has no nodes in JSON")

        # Check specific node connections (pass the list of nodes)
        self.check_net_nodes(gnd_net, "D1")
        self.check_net_nodes(gnd_net, "U1")

        # Check Net-(D1-A) net nodes
        self.assertIn(
            "Net-(D1-A)", self.json_data["nets"], "Net-(D1-A) net missing from JSON"
        )
        d1a_net = self.json_data["nets"]["Net-(D1-A)"]

        # Check that Net-(D1-A) net has nodes (d1a_net is the list of nodes in Structure A)
        self.assertIsInstance(
            d1a_net, list, "Net-(D1-A) net data should be a list (Structure A)"
        )
        self.assertGreater(len(d1a_net), 0, "Net-(D1-A) net has no nodes in JSON")

        # Check specific node connections (pass the list of nodes)
        self.check_net_nodes(d1a_net, "D1", "2")
        self.check_net_nodes(d1a_net, "R1", "2")

    def test_pin_types(self):
        """Test that pin types are correctly preserved."""
        # Check for power_in pin type
        power_in_found = False
        for net_name, net in self.json_data["nets"].items():
            for node in net:  # Iterate directly over the list of nodes
                if node["pin"].get("type") == "power_in":
                    power_in_found = True
                    break
            if power_in_found:
                break
        self.assertTrue(power_in_found, "No power_in pin type found in JSON")

        # Check for input pin type
        input_found = False
        for net_name, net in self.json_data["nets"].items():
            for node in net:  # Iterate directly over the list of nodes
                if node["pin"].get("type") == "input":
                    input_found = True
                    break
            if input_found:
                break
        self.assertTrue(input_found, "No input pin type found in JSON")

        # Check for bidirectional pin type
        bidirectional_found = False
        for net_name, net in self.json_data["nets"].items():
            for node in net:  # Iterate directly over the list of nodes
                if node["pin"].get("type") == "bidirectional":
                    bidirectional_found = True
                    break
            if bidirectional_found:
                break
        self.assertTrue(bidirectional_found, "No bidirectional pin type found in JSON")

        # Check for passive pin type
        passive_found = False
        for net_name, net in self.json_data["nets"].items():
            for node in net:  # Iterate directly over the list of nodes
                if node["pin"].get("type") == "passive":
                    passive_found = True
                    break
            if passive_found:
                break
        self.assertTrue(passive_found, "No passive pin type found in JSON")

    def test_unconnected_pins(self):
        """Test that unconnected pins are correctly handled."""
        # Check for unconnected nets
        unconnected_nets = [
            net_name
            for net_name in self.json_data["nets"]
            if "unconnected-" in net_name
        ]
        self.assertGreater(
            len(unconnected_nets), 0, "No unconnected nets found in JSON"
        )

        # Check that unconnected nets have nodes
        for net_name in unconnected_nets:
            net = self.json_data["nets"][net_name]
            # net is the list of nodes in Structure A
            self.assertIsInstance(
                net, list, f"{net_name} net data should be a list (Structure A)"
            )
            self.assertGreater(len(net), 0, f"{net_name} net has no nodes in JSON")

    def test_round_trip_conversion(self):
        """
        Test the round-trip conversion by comparing the original netlist with the exported one.
        """
        # Skip if the exported netlist doesn't exist
        if not self.EXPORTED_NETLIST_FILE.exists():
            self.skipTest("Exported netlist doesn't exist")

        # Read exported netlist
        exported_content = self.EXPORTED_NETLIST_FILE.read_text(encoding="utf-8")

        # Extract component references from both netlists
        original_refs = re.findall(r'\(comp \(ref "([^"]+)"\)', self.netlist_content)
        exported_refs = re.findall(r'\(comp \(ref "([^"]+)"\)', exported_content)

        # Compare component references
        self.assertEqual(
            set(original_refs),
            set(exported_refs),
            "Component references don't match between original and exported netlists",
        )

        # Extract net names from both netlists
        original_nets = re.findall(
            r'\(net \(code "[^"]+"\) \(name "([^"]+)"\)', self.netlist_content
        )
        exported_nets = re.findall(
            r'\(net \(code "[^"]+"\) \(name "([^"]+)"\)', exported_content
        )

        # Compare net names
        self.assertEqual(
            set(original_nets),
            set(exported_nets),
            "Net names don't match between original and exported netlists",
        )

        # Extract net-to-component connections from both netlists
        original_connections = {}
        exported_connections = {}

        # Find all net blocks in original netlist
        net_blocks_original = re.findall(
            r'\(net \(code "[^"]+"\) \(name "([^"]+)"\)(.*?)\)',
            self.netlist_content,
            re.DOTALL,
        )
        for net_name, net_content in net_blocks_original:
            # Find all node references in this net
            nodes = re.findall(
                r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', net_content
            )
            original_connections[net_name] = [f"{ref}:{pin}" for ref, pin in nodes]

        # Find all net blocks in exported netlist
        net_blocks_exported = re.findall(
            r'\(net \(code "[^"]+"\) \(name "([^"]+)"\)(.*?)\)',
            exported_content,
            re.DOTALL,
        )
        for net_name, net_content in net_blocks_exported:
            # Find all node references in this net
            nodes = re.findall(
                r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', net_content
            )
            exported_connections[net_name] = [f"{ref}:{pin}" for ref, pin in nodes]

        # Compare net-to-component connections
        for net_name in original_nets:
            if net_name in original_connections and net_name in exported_connections:
                self.assertEqual(
                    set(original_connections[net_name]),
                    set(exported_connections[net_name]),
                    f"Connections for net '{net_name}' don't match",
                )


if __name__ == "__main__":
    unittest.main()
