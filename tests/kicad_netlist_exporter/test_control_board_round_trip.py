import json
import unittest
from pathlib import Path

import pytest

from circuit_synth.kicad.netlist_exporter import convert_json_to_netlist
from circuit_synth.kicad.sheet_hierarchy_manager import SheetHierarchyManager


class TestControlBoardRoundTrip(unittest.TestCase):
    """
    Tests round-trip conversion of control_board.net:
    1. Import control_board.net to JSON using netlist_importer
    2. Export that JSON back to a netlist using netlist_exporter
    3. Compare original and generated netlists
    """

    @classmethod
    def setUpClass(cls):
        # Base directory is project root
        cls.BASE_DIR = Path(__file__).parent.parent.parent.parent.parent

        # Create output directory if it doesn't exist
        cls.OUTPUT_DIR = cls.BASE_DIR / "test_output"
        cls.OUTPUT_DIR.mkdir(exist_ok=True)

        # Input/output paths - use existing files
        cls.INPUT_JSON_PATH = (
            cls.OUTPUT_DIR / "netlist2_output.json"
        )  # Use existing JSON file
        cls.OUTPUT_NETLIST_PATH = cls.OUTPUT_DIR / "control_board_exported.net"
        cls.ORIGINAL_NETLIST_PATH = (
            cls.BASE_DIR
            / "tests"
            / "test_data"
            / "kicad9"
            / "netlists"
            / "netlist2.net"
        )  # Use matching netlist

    @pytest.mark.skip(
        reason="Test depends on generated JSON files from other test runs - core round-trip functionality tested in other netlist tests"
    )
    def test_round_trip_conversion(self):
        """
        Test the round-trip conversion of control_board.net through JSON and back.
        Verifies that all essential information is preserved.
        """
        # Skip if files don't exist
        if not self.INPUT_JSON_PATH.exists():
            self.skipTest("Input JSON file doesn't exist")
        if not self.ORIGINAL_NETLIST_PATH.exists():
            self.skipTest("Original netlist file doesn't exist")

        # Convert JSON back to netlist
        convert_json_to_netlist(self.INPUT_JSON_PATH, self.OUTPUT_NETLIST_PATH)
        self.assertTrue(self.OUTPUT_NETLIST_PATH.exists())

        # Read original and generated netlists
        original_content = self.ORIGINAL_NETLIST_PATH.read_text(encoding="utf-8")
        generated_content = self.OUTPUT_NETLIST_PATH.read_text(encoding="utf-8")

        # Compare component references and values
        original_refs = self._extract_component_refs(original_content)
        generated_refs = self._extract_component_refs(generated_content)
        self.assertEqual(
            set(original_refs),
            set(generated_refs),
            "Component references don't match between original and generated netlists",
        )

        # Compare component values
        original_values = self._extract_component_values(original_content)
        generated_values = self._extract_component_values(generated_content)
        self.assertEqual(
            original_values,
            generated_values,
            "Component values don't match between original and generated netlists",
        )

        # Compare net names with hierarchy handling
        original_nets = self._extract_hierarchical_nets(original_content)
        generated_nets = self._extract_hierarchical_nets(generated_content)
        self.assertEqual(
            set(original_nets),
            set(generated_nets),
            "Net names don't match between original and generated netlists",
        )

        # Compare net-to-component connections with pin types
        original_connections = self._extract_net_connections_with_types(
            original_content
        )
        generated_connections = self._extract_net_connections_with_types(
            generated_content
        )

        # Compare connections for each net
        for net_name in original_nets:
            orig_conns = original_connections.get(net_name, [])
            gen_conns = generated_connections.get(net_name, [])
            self.assertEqual(
                set(orig_conns),
                set(gen_conns),
                f"Connections for net '{net_name}' don't match",
            )

        # Verify power nets are properly handled
        power_nets = {"VCC", "GND", "+3.3V", "+5V"}
        for net in power_nets:
            if net in original_nets:
                self.assertIn(
                    net,
                    generated_nets,
                    f"Power net '{net}' missing from generated netlist",
                )
                # Verify power net connections match
                self.assertEqual(
                    set(original_connections.get(net, [])),
                    set(generated_connections.get(net, [])),
                    f"Connections for power net '{net}' don't match",
                )

    def _extract_component_refs(self, netlist_content):
        """Extract component references from netlist content."""
        import re

        refs = re.findall(r'\(comp \(ref "([^"]+)"\)', netlist_content)
        return refs

    def _extract_component_values(self, netlist_content):
        """Extract component references and their values."""
        import re

        values = {}
        comp_blocks = re.findall(
            r'\(comp \(ref "([^"]+)".*?\(value "([^"]+)".*?\)',
            netlist_content,
            re.DOTALL,
        )
        for ref, value in comp_blocks:
            values[ref] = value
        return values

    def _extract_hierarchical_nets(self, netlist_content):
        """Extract net names with hierarchy information."""
        import re

        nets = []
        net_blocks = re.findall(
            r'\(net \(code "[^"]+"\) \(name "([^"]+)".*?\)', netlist_content, re.DOTALL
        )

        for net in net_blocks:
            # Handle hierarchical paths in net names
            normalized_net = net.replace("//", "/")  # Normalize path separators
            nets.append(normalized_net)

        return nets

    def _extract_net_connections_with_types(self, netlist_content):
        """Extract net-to-component connections including pin types."""
        import re

        connections = {}

        # Find all net blocks
        net_blocks = re.findall(
            r'\(net \(code "[^"]+"\) \(name "([^"]+)".*?\)', netlist_content, re.DOTALL
        )

        for net_name in net_blocks:
            # Find the full net block
            net_block = re.search(
                f'\\(net \\(code "[^"]+"\\) \\(name "{net_name}".*?\\)',
                netlist_content,
                re.DOTALL,
            )
            if net_block:
                # Extract nodes with pin types
                nodes = re.findall(
                    r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)(?: \(pintype "([^"]+)"\))?',
                    net_block.group(0),
                )
                connections[net_name] = [
                    f"{ref}:{pin}:{pintype if pintype else 'passive'}"
                    for ref, pin, pintype in nodes
                ]

        return connections


if __name__ == "__main__":
    unittest.main()
