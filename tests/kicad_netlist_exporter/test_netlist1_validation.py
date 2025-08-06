import json
import re
from pathlib import Path

from .test_netlist_validation_base import NetlistValidationBase


class TestNetlist1Validation(NetlistValidationBase):
    """
    Thorough test for validating that netlist1_output.json correctly represents
    the original netlist1.net file.
    """

    @classmethod
    def setUpClass(cls):
        # Base directory: project root (i.e. two parents up from this file)
        cls.BASE_DIR = Path(__file__).parent.parent

        # Test data and output directories
        cls.TEST_DATA_DIR = cls.BASE_DIR / "test_data" / "kicad9" / "netlists"
        cls.TEST_OUTPUT_DIR = cls.BASE_DIR / "test_output"

        # Specific files for this test
        cls.NETLIST_FILE = cls.TEST_DATA_DIR / "netlist1.net"
        cls.JSON_FILE = cls.TEST_OUTPUT_DIR / "netlist1_output.json"
        cls.EXPORTED_NETLIST_FILE = cls.TEST_OUTPUT_DIR / "netlist1_exported.net"

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
        self.assertEqual(self.json_data["name"], "netlist1", "Incorrect netlist name")

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
        key_components = ["C1", "R1", "R2"]
        for comp_ref in key_components:
            self.assertIn(
                comp_ref, json_components, f"Key component {comp_ref} missing from JSON"
            )

    def test_component_properties(self):
        """Test that component properties are correctly extracted."""
        # Test C1 component properties
        self.assert_component_property(
            self.json_data["components"], "C1", "reference", "C1"
        )
        self.assert_component_property(
            self.json_data["components"], "C1", "value", "0.1uF"
        )
        self.assert_component_property(
            self.json_data["components"],
            "C1",
            "footprint",
            "Capacitor_SMD:C_0603_1608Metric",
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

        # Test R2 component properties
        self.assert_component_property(
            self.json_data["components"], "R2", "reference", "R2"
        )
        self.assert_component_property(
            self.json_data["components"], "R2", "value", "1k"
        )
        self.assert_component_property(
            self.json_data["components"],
            "R2",
            "footprint",
            "Resistor_SMD:R_0603_1608Metric",
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

        # Verify all nets from netlist are in JSON, accounting for hierarchical naming
        for net_name in netlist_nets:
            # For hierarchical nets, the JSON might store them without the leading slash
            # but with is_hierarchical=true and hierarchical_name set correctly
            if net_name.startswith("/"):
                local_name = net_name[1:]  # Remove leading slash
                self.assertTrue(
                    net_name in json_nets or local_name in json_nets,
                    f"Net {net_name} missing from JSON (checked both {net_name} and {local_name})",
                )
            else:
                self.assertIn(net_name, json_nets, f"Net {net_name} missing from JSON")

        # Verify key nets, accounting for hierarchical naming
        key_nets = {
            "+3V3": ["+3V3"],
            "/OUTPUT": ["/OUTPUT", "OUTPUT"],  # Check both forms
            "GND": ["GND"],
        }
        for original_name, possible_names in key_nets.items():
            self.assertTrue(
                any(name in json_nets for name in possible_names),
                f"Key net {original_name} missing from JSON (checked {possible_names})",
            )

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
        self.check_net_nodes(v3v3_net, "R1", "1")

        # Check OUTPUT net nodes (might be stored as "OUTPUT" or "/OUTPUT")
        output_net_key = "/OUTPUT" if "/OUTPUT" in self.json_data["nets"] else "OUTPUT"
        self.assertTrue(
            "/OUTPUT" in self.json_data["nets"] or "OUTPUT" in self.json_data["nets"],
            "OUTPUT net missing from JSON (checked both /OUTPUT and OUTPUT)",
        )
        output_net = self.json_data["nets"][output_net_key]

        # Check that OUTPUT net has nodes (output_net is the list of nodes in Structure A)
        self.assertIsInstance(
            output_net, list, "OUTPUT net data should be a list (Structure A)"
        )
        self.assertGreater(len(output_net), 0, "OUTPUT net has no nodes in JSON")

        # Check specific node connections (pass the list of nodes)
        self.check_net_nodes(output_net, "R1", "2")
        self.check_net_nodes(output_net, "R2", "1")

        # Check GND net nodes
        self.assertIn("GND", self.json_data["nets"], "GND net missing from JSON")
        gnd_net = self.json_data["nets"]["GND"]

        # Check that GND net has nodes (gnd_net is the list of nodes in Structure A)
        self.assertIsInstance(
            gnd_net, list, "GND net data should be a list (Structure A)"
        )
        self.assertGreater(len(gnd_net), 0, "GND net has no nodes in JSON")

        # Check specific node connections (pass the list of nodes)
        self.check_net_nodes(gnd_net, "C1", "2")
        self.check_net_nodes(gnd_net, "R2", "2")

    def test_pin_types(self):
        """Test that pin types are correctly preserved."""
        # Check passive pin type for resistors and capacitors
        # Handle hierarchical net names that might be stored without leading slash
        net_names_to_check = []
        for net_name in ["+3V3", "/OUTPUT", "GND"]:
            if net_name.startswith("/") and net_name not in self.json_data["nets"]:
                # Try without the leading slash
                local_name = net_name[1:]
                if local_name in self.json_data["nets"]:
                    net_names_to_check.append(local_name)
                else:
                    self.fail(
                        f"Net {net_name} not found in JSON (tried both {net_name} and {local_name})"
                    )
            else:
                if net_name in self.json_data["nets"]:
                    net_names_to_check.append(net_name)
                else:
                    self.fail(f"Net {net_name} not found in JSON")

        for net_name in net_names_to_check:
            net = self.json_data["nets"][net_name]
            # Iterate directly over the list of nodes (net is the list in Structure A)
            for node in net:
                if node.get("component") in ["R1", "R2", "C1"]:
                    self.assertEqual(
                        node.get("pin", {}).get("type"),
                        "passive",
                        f"{node.get('component')} pin type should be passive",
                    )

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

        # Compare net names after standardizing (remove leading '/' for comparison)
        standardize = lambda name: name[1:] if name.startswith("/") else name
        standardized_original_nets = {standardize(n) for n in original_nets}
        standardized_exported_nets = {standardize(n) for n in exported_nets}
        self.assertEqual(
            standardized_original_nets,
            standardized_exported_nets,
            "Standardized net names don't match between original and exported netlists",
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
