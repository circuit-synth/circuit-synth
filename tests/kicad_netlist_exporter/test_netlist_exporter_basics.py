import json
import os
import unittest
from pathlib import Path

from circuit_synth.kicad.netlist_exporter import PinType, convert_json_to_netlist


class TestKicadNetlistExporter(unittest.TestCase):
    """
    Tests the KiCad netlist exporter for converting circuit-synth JSON files
    back to KiCad netlist (.net) files.
    """

    @classmethod
    def setUpClass(cls):
        # Base directory: tests/ (i.e. three parents up from this file)
        cls.BASE_DIR = Path(__file__).parent.parent

        # Create output directory if it doesn't exist
        cls.OUTPUT_DIR = cls.BASE_DIR / "test_output"
        cls.OUTPUT_DIR.mkdir(exist_ok=True)

        # Input JSON paths (from importer tests)
        cls.INPUT1_JSON_PATH = cls.OUTPUT_DIR / "netlist1_output.json"
        cls.INPUT2_JSON_PATH = cls.OUTPUT_DIR / "netlist2_output.json"

        # Output netlist paths
        cls.OUTPUT1_NETLIST_PATH = cls.OUTPUT_DIR / "netlist1_exported.net"
        cls.OUTPUT2_NETLIST_PATH = cls.OUTPUT_DIR / "netlist2_exported.net"

        # Original netlist paths for comparison
        cls.ORIGINAL1_NETLIST_PATH = (
            cls.BASE_DIR / "test_data" / "kicad9" / "netlists" / "netlist1.net"
        )
        cls.ORIGINAL2_NETLIST_PATH = (
            cls.BASE_DIR / "test_data" / "kicad9" / "netlists" / "netlist2.net"
        )

    def test_export_netlist1(self):
        """
        Test exporting netlist1_output.json back to a KiCad netlist file,
        verifying structure, components, nets, etc.
        """
        # 1) Verify input JSON file presence
        self.assertTrue(
            self.INPUT1_JSON_PATH.is_file(),
            f"Missing input JSON file: {self.INPUT1_JSON_PATH}",
        )

        # 2) Convert netlist1_output.json => netlist1_exported.net
        convert_json_to_netlist(self.INPUT1_JSON_PATH, self.OUTPUT1_NETLIST_PATH)
        self.assertTrue(self.OUTPUT1_NETLIST_PATH.exists())

        # 3) Parse the generated netlist and verify its structure
        netlist_content = self.OUTPUT1_NETLIST_PATH.read_text(encoding="utf-8")

        # ---- Basic structure checks ----
        self.assertIn("(export", netlist_content)
        self.assertIn("(design", netlist_content)
        self.assertIn("(components", netlist_content)
        self.assertIn("(nets", netlist_content)

        # ---- Check components ----
        self.assertIn('(comp (ref "C1")', netlist_content)
        self.assertIn('(comp (ref "R1")', netlist_content)
        self.assertIn('(comp (ref "R2")', netlist_content)

        self.assertIn('(value "0.1uF")', netlist_content)
        self.assertIn('(value "10k")', netlist_content)
        self.assertIn('(value "1k")', netlist_content)

        self.assertIn('(footprint "Capacitor_SMD:C_0603_1608Metric")', netlist_content)
        self.assertIn('(footprint "Resistor_SMD:R_0603_1608Metric")', netlist_content)

        # ---- Check nets ----
        # Expect net code "0" as it's currently hardcoded in the exporter
        self.assertIn('(net (code "1") (name "+3V3")', netlist_content)
        # Expect simplified name "OUTPUT" for top-level hierarchical net
        self.assertIn('(net (code "2") (name "OUTPUT")', netlist_content)
        self.assertIn('(net (code "3") (name "GND")', netlist_content)

        # Check net nodes
        self.assertIn(
            '(node (ref "R1") (pin "1") (pintype "passive"))', netlist_content
        )
        self.assertIn(
            '(node (ref "C1") (pin "1") (pintype "passive"))', netlist_content
        )
        self.assertIn(
            '(node (ref "R1") (pin "2") (pintype "passive"))', netlist_content
        )
        self.assertIn(
            '(node (ref "R2") (pin "1") (pintype "passive"))', netlist_content
        )
        self.assertIn(
            '(node (ref "C1") (pin "2") (pintype "passive"))', netlist_content
        )
        self.assertIn(
            '(node (ref "R2") (pin "2") (pintype "passive"))', netlist_content
        )

        # ---- Check properties ----
        self.assertIn("(source", netlist_content)
        self.assertIn("(date", netlist_content)
        self.assertIn("(tool", netlist_content)

        print(
            f"JSON => netlist conversion output written to: {self.OUTPUT1_NETLIST_PATH.resolve()}"
        )

    def test_export_netlist2(self):
        """
        Test exporting netlist2_output.json back to a KiCad netlist file,
        verifying structure, components, nets, pin types, etc.
        Tests proper handling of different pin types, including:
        - power_in, power_out, input, output, bidirectional, passive, no_connect
        - Components including microcontroller, LEDs, resistors, and unconnected pins
        """
        # 1) Verify input JSON file presence
        self.assertTrue(
            self.INPUT2_JSON_PATH.is_file(),
            f"Missing input JSON file: {self.INPUT2_JSON_PATH}",
        )

        # 2) Convert netlist2_output.json => netlist2_exported.net
        convert_json_to_netlist(self.INPUT2_JSON_PATH, self.OUTPUT2_NETLIST_PATH)
        self.assertTrue(self.OUTPUT2_NETLIST_PATH.exists())

        # 3) Parse the generated netlist and verify its structure
        netlist_content = self.OUTPUT2_NETLIST_PATH.read_text(encoding="utf-8")

        # ---- Basic structure checks ----
        self.assertIn("(export", netlist_content)
        self.assertIn("(design", netlist_content)
        self.assertIn("(components", netlist_content)
        self.assertIn("(nets", netlist_content)

        # ---- Check components ----
        self.assertIn('(comp (ref "D1")', netlist_content)
        self.assertIn('(comp (ref "R1")', netlist_content)
        self.assertIn('(comp (ref "U1")', netlist_content)

        self.assertIn('(value "LED")', netlist_content)
        self.assertIn('(value "10k")', netlist_content)
        self.assertIn('(value "ESP32-C6-MINI-1")', netlist_content)

        self.assertIn('(footprint "LED_SMD:LED_0603_1608Metric")', netlist_content)
        self.assertIn('(footprint "Resistor_SMD:R_0603_1608Metric")', netlist_content)
        self.assertIn('(footprint "RF_Module:ESP32-C6-MINI-1")', netlist_content)

        # ---- Check nets ----
        # Expect net code "0"
        self.assertIn('(net (code "1") (name "+3V3")', netlist_content)
        self.assertIn('(net (code "2") (name "GND")', netlist_content)
        self.assertIn('(net (code "3") (name "Net-(D1-A)")', netlist_content)

        # ---- Check pin types ----
        # Check for specific pin types in connected nets
        self.assertIn(
            '(node (ref "U1") (pin "1") (pintype "power_in") (pinfunction "GND"))',
            netlist_content,
        )
        self.assertIn(
            '(node (ref "U1") (pin "17") (pintype "bidirectional") (pinfunction "IO12"))',
            netlist_content,
        )

        # ---- Check unconnected pins ----
        # Verify unconnected pins are properly handled with correct pin types
        self.assertIn(
            '(net (code "5") (name "unconnected-(U1-EN-Pad8)")', netlist_content
        )
        self.assertIn(
            '(node (ref "(U1") (pin "None") (pintype "passive"))', netlist_content
        )

        print(
            f"JSON => netlist conversion output written to: {self.OUTPUT2_NETLIST_PATH.resolve()}"
        )

    def test_round_trip_conversion(self):
        """
        Test the round-trip conversion:
        1. Original netlist -> JSON (using importer)
        2. JSON -> Generated netlist (using exporter)
        3. Compare key elements between original and generated netlists

        This test ensures that the exporter correctly preserves all essential
        information from the original netlist.
        """
        # Skip if the exported netlist doesn't exist
        if not self.OUTPUT1_NETLIST_PATH.exists():
            self.skipTest(
                "Exported netlist doesn't exist - run test_export_netlist1 first"
            )

        # Read original and generated netlists
        original_content = self.ORIGINAL1_NETLIST_PATH.read_text(encoding="utf-8")
        generated_content = self.OUTPUT1_NETLIST_PATH.read_text(encoding="utf-8")

        # Compare component references
        original_refs = self._extract_component_refs(original_content)
        generated_refs = self._extract_component_refs(generated_content)
        self.assertEqual(
            set(original_refs),
            set(generated_refs),
            "Component references don't match between original and generated netlists",
        )

        # Compare net names
        original_nets_raw = self._extract_net_names(original_content)
        generated_nets_raw = self._extract_net_names(generated_content)
        # Normalize names by removing leading '/' before comparing sets
        original_nets_norm = {name.lstrip("/") for name in original_nets_raw}
        generated_nets_norm = {name.lstrip("/") for name in generated_nets_raw}
        self.assertEqual(
            original_nets_norm,
            generated_nets_norm,
            f"Net names don't match between original ({original_nets_raw}) and generated ({generated_nets_raw}) netlists after normalization",
        )

        # Compare net-to-component connections
        original_connections = self._extract_net_connections(original_content)
        generated_connections = self._extract_net_connections(generated_content)

        # Compare connections using normalized names
        for original_net_name in original_nets_raw:
            normalized_name = original_net_name.lstrip("/")
            # Find the corresponding generated name (could be original or normalized)
            generated_net_name = (
                original_net_name
                if original_net_name in generated_connections
                else normalized_name
            )

            if (
                original_net_name in original_connections
                and generated_net_name in generated_connections
            ):
                self.assertEqual(
                    set(original_connections[original_net_name]),
                    set(generated_connections[generated_net_name]),
                    f"Connections for net '{original_net_name}' (compared as '{normalized_name}') don't match",
                )
            elif original_net_name in original_connections:
                self.fail(
                    f"Net '{original_net_name}' found in original connections but not in generated connections (checked as '{generated_net_name}')"
                )

    def _extract_component_refs(self, netlist_content):
        """Helper method to extract component references from netlist content"""
        import re

        refs = re.findall(r'\(comp \(ref "([^"]+)"\)', netlist_content)
        return refs

    def _extract_net_names(self, netlist_content):
        """Helper method to extract net names from netlist content"""
        import re

        nets = re.findall(r'\(net \(code "[^"]+"\) \(name "([^"]+)"\)', netlist_content)
        return nets

    def _extract_net_connections(self, netlist_content):
        """Helper method to extract net-to-component connections from netlist content"""
        import re

        connections = {}

        # Find all net blocks
        net_blocks = re.findall(
            r'\(net \(code "[^"]+"\) \(name "([^"]+)"\)(.*?)\)',
            netlist_content,
            re.DOTALL,
        )

        for net_name, net_content in net_blocks:
            # Find all node references in this net
            nodes = re.findall(
                r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', net_content
            )
            connections[net_name] = [f"{ref}:{pin}" for ref, pin in nodes]

        return connections


if __name__ == "__main__":
    unittest.main()
