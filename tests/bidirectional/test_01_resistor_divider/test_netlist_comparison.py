#!/usr/bin/env python3
"""
Pytest test for resistor divider circuit generation and netlist comparison.

This test validates that the generated KiCad project produces an electrically
equivalent netlist to the reference project by:
1. Running the circuit generation script
2. Generating netlists for both reference and generated projects using kicad-cli
3. Parsing and comparing the netlists for electrical equivalence
"""

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest


class NetlistParser:
    """Parser for KiCad S-expression netlist format."""

    def __init__(self, netlist_content: str):
        self.content = netlist_content
        self.components = {}
        self.nets = {}
        self.parse()

    def parse(self):
        """Parse the netlist content into components and nets."""
        # Parse components - updated pattern for actual KiCad netlist format
        comp_pattern = r'\(comp\s+\(ref\s+"([^"]+)"\)\s+\(value\s+"([^"]*)"\)'
        components = re.findall(comp_pattern, self.content, re.MULTILINE | re.DOTALL)

        for ref, value in components:
            self.components[ref] = {
                "value": value,
                "footprint": "",  # Footprint not always in netlist
            }

        # Parse nets - improved pattern to capture complete net sections
        # Find the start of the nets section
        nets_start = self.content.find("(nets")
        if nets_start == -1:
            return  # No nets section found

        nets_content = self.content[nets_start:]

        # Pattern to match each complete net definition including all nodes
        net_pattern = r'\(net\s+\(code\s+"?(\d+)"?\)\s+\(name\s+"([^"]+)"\)[^)]*?(?:\(node[^)]+\)[^)]*?)*\)'
        net_matches = re.findall(net_pattern, nets_content, re.MULTILINE | re.DOTALL)

        # If the above doesn't work, try a different approach - split by net boundaries
        if not net_matches:
            # Alternative parsing: find each net block manually
            net_blocks = re.split(r"(?=\(net\s+\(code)", nets_content)[
                1:
            ]  # Skip empty first element

            for block in net_blocks:
                # Extract code and name from the start of each block
                code_match = re.search(r'\(code\s+"?(\d+)"?\)', block)
                name_match = re.search(r'\(name\s+"([^"]+)"\)', block)

                if code_match and name_match:
                    code = code_match.group(1)
                    name = name_match.group(2)

                    # Extract all nodes from this block
                    node_pattern = r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)'
                    nodes = re.findall(node_pattern, block)

                    # Create a set of (component_ref, pin) tuples for this net
                    net_connections = set(nodes)
                    self.nets[name] = {"code": code, "connections": net_connections}
        else:
            # Use the original approach if regex worked
            for code, name in net_matches:
                # Find the full net content for this specific net
                net_start = nets_content.find(f'(net (code "{code}") (name "{name}")')
                if net_start == -1:
                    net_start = nets_content.find(f'(net (code {code}) (name "{name}")')

                if net_start != -1:
                    # Find the end of this net definition
                    net_end = nets_content.find("(net (code", net_start + 1)
                    if net_end == -1:
                        net_content = nets_content[net_start:]
                    else:
                        net_content = nets_content[net_start:net_end]

                    # Extract nodes from this specific net content
                    node_pattern = r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)'
                    nodes = re.findall(node_pattern, net_content)

                    # Create a set of (component_ref, pin) tuples for this net
                    net_connections = set(nodes)
                    self.nets[name] = {"code": code, "connections": net_connections}

    def get_component_types(self) -> Dict[str, str]:
        """Get mapping of component reference to type (symbol:value)."""
        return {
            ref: f"{comp.get('value', 'unknown')}"
            for ref, comp in self.components.items()
        }

    def get_net_connections(self) -> Dict[str, Set[Tuple[str, str]]]:
        """Get mapping of net name to set of (component_ref, pin) connections."""
        return {name: net["connections"] for name, net in self.nets.items()}

    def normalize_for_comparison(self) -> Dict:
        """Create a normalized representation for comparison."""
        return {
            "components": self.get_component_types(),
            "nets": self.get_net_connections(),
        }


def run_kicad_cli_netlist_export(schematic_path: Path, output_path: Path) -> bool:
    """
    Run kicad-cli to export netlist from schematic.

    Args:
        schematic_path: Path to .kicad_sch file
        output_path: Path where netlist should be saved

    Returns:
        True if successful, False otherwise
    """
    try:
        cmd = [
            "kicad-cli",
            "sch",
            "export",
            "netlist",
            "--format",
            "kicadsexpr",
            "--output",
            str(output_path),
            str(schematic_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        return output_path.exists()

    except subprocess.CalledProcessError as e:
        pytest.fail(f"kicad-cli failed: {e.stderr}")
        return False
    except FileNotFoundError:
        pytest.fail(
            "kicad-cli not found. Please ensure KiCad is installed and kicad-cli is in PATH."
        )
        return False


def compare_netlists(
    reference_netlist: NetlistParser, generated_netlist: NetlistParser
) -> Tuple[bool, List[str]]:
    """
    Compare two netlists for the specific resistor divider circuit.

    Expected circuit:
    - R1 and R2 resistors
    - VIN, MID, GND nets
    - R1 pin 1 → VIN, R1 pin 2 → MID
    - R2 pin 1 → MID, R2 pin 2 → GND

    Args:
        reference_netlist: Parsed reference netlist
        generated_netlist: Parsed generated netlist

    Returns:
        Tuple of (is_equivalent, list_of_differences)
    """
    differences = []

    # Check for exactly R1 and R2 components
    expected_components = {"R1", "R2"}
    gen_components = set(generated_netlist.components.keys())

    if gen_components != expected_components:
        differences.append(
            f"Expected components {expected_components}, got {gen_components}"
        )

    # Check for correct net names (normalize net names by removing leading slash)
    def normalize_net_name(name):
        return name.lstrip("/")

    expected_nets = {"VIN", "MID", "GND"}
    gen_net_names = {normalize_net_name(name) for name in generated_netlist.nets.keys()}

    if gen_net_names != expected_nets:
        differences.append(f"Expected nets {expected_nets}, got {gen_net_names}")

    # Check specific connections
    gen_nets = generated_netlist.nets

    # Normalize net names in connections
    normalized_nets = {}
    for net_name, net_data in gen_nets.items():
        normalized_name = normalize_net_name(net_name)
        normalized_nets[normalized_name] = net_data["connections"]

    # Define expected connections
    expected_connections = {
        "VIN": {("R1", "1")},
        "MID": {("R1", "2"), ("R2", "1")},
        "GND": {("R2", "2")},
    }

    # Check each expected connection
    for net_name, expected_conn in expected_connections.items():
        if net_name not in normalized_nets:
            differences.append(f"Net '{net_name}' not found in generated netlist")
            continue

        actual_conn = normalized_nets[net_name]
        if actual_conn != expected_conn:
            differences.append(
                f"Net '{net_name}' connections mismatch: expected {expected_conn}, got {actual_conn}"
            )

    # Check that no extra connections exist
    for net_name, actual_conn in normalized_nets.items():
        if net_name in expected_connections:
            continue  # Already checked above
        differences.append(
            f"Unexpected net '{net_name}' with connections {actual_conn}"
        )

    is_equivalent = len(differences) == 0
    return is_equivalent, differences


def test_resistor_divider_netlist_comparison():
    """
    Test that the generated resistor divider circuit produces an electrically
    equivalent netlist to the reference project.
    """
    # Define paths
    test_dir = Path(__file__).parent
    circuit_script = test_dir / "resistor_divider.py"
    reference_dir = test_dir / "reference_resistor_divider"

    # Verify input files exist
    if not circuit_script.exists():
        pytest.fail(f"Circuit script not found: {circuit_script}")

    if not reference_dir.exists():
        pytest.fail(f"Reference directory not found: {reference_dir}")

    # Find reference schematic file
    reference_sch_files = list(reference_dir.glob("*.kicad_sch"))
    if not reference_sch_files:
        pytest.fail(
            f"No .kicad_sch files found in reference directory: {reference_dir}"
        )

    # Use the main project schematic (not any sub-schematics)
    reference_sch = None
    for sch_file in reference_sch_files:
        # Look for the main project file (typically matches directory name or is the largest)
        if sch_file.stem == reference_dir.name or sch_file.stem == "resistor_divider":
            reference_sch = sch_file
            break

    if not reference_sch:
        # Fallback to first schematic found
        reference_sch = reference_sch_files[0]

    # Create temporary directory for generated project
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Run the circuit generation script
        try:
            # Change to temp directory and run script
            original_cwd = Path.cwd()
            try:
                # Copy the script to temp directory to avoid path issues
                temp_script = temp_path / "resistor_divider.py"
                shutil.copy2(circuit_script, temp_script)

                # Run the script from temp directory
                result = subprocess.run(
                    ["python", str(temp_script)],
                    cwd=temp_path,
                    capture_output=True,
                    text=True,
                    check=True,
                )

            finally:
                pass  # Keep original directory

        except subprocess.CalledProcessError as e:
            pytest.fail(f"Circuit generation failed: {e.stderr}")

        # Find generated schematic file
        generated_sch_files = list(temp_path.glob("**/*.kicad_sch"))
        if not generated_sch_files:
            pytest.fail(f"No .kicad_sch files generated in: {temp_path}")

        # Use the main generated schematic
        generated_sch = None
        for sch_file in generated_sch_files:
            if sch_file.stem == "resistor_divider":
                generated_sch = sch_file
                break

        if not generated_sch:
            generated_sch = generated_sch_files[0]

        # Generate netlists using kicad-cli
        reference_netlist_path = temp_path / "reference.net"
        generated_netlist_path = temp_path / "generated.net"

        # Export reference netlist
        if not run_kicad_cli_netlist_export(reference_sch, reference_netlist_path):
            pytest.fail(f"Failed to export reference netlist from: {reference_sch}")

        # Export generated netlist
        if not run_kicad_cli_netlist_export(generated_sch, generated_netlist_path):
            pytest.fail(f"Failed to export generated netlist from: {generated_sch}")

        # Read and parse netlists
        with open(reference_netlist_path, "r") as f:
            reference_content = f.read()

        with open(generated_netlist_path, "r") as f:
            generated_content = f.read()

        reference_parser = NetlistParser(reference_content)
        generated_parser = NetlistParser(generated_content)

        # Compare netlists
        is_equivalent, differences = compare_netlists(
            reference_parser, generated_parser
        )

        # Assert equivalence
        if not is_equivalent:
            error_msg = "Generated netlist does not match reference netlist:\n"
            error_msg += "\n".join(f"  - {diff}" for diff in differences)
            error_msg += f"\n\nReference netlist:\n{reference_content[:500]}..."
            error_msg += f"\n\nGenerated netlist:\n{generated_content[:500]}..."
            pytest.fail(error_msg)

        # If we get here, the test passed
        print(f"✓ Netlist comparison successful!")
        print(f"  - Reference schematic: {reference_sch}")
        print(f"  - Generated schematic: {generated_sch}")
        print(f"  - Components matched: {len(reference_parser.components)}")
        print(f"  - Nets matched: {len(reference_parser.nets)}")


if __name__ == "__main__":
    # Allow running directly for debugging
    test_resistor_divider_netlist_comparison()
