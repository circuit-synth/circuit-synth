#!/usr/bin/env python3
"""
Automated test for 31_isolated_component bidirectional test.

Tests CRITICAL early-stage design workflow: handling of isolated components
with no net connections.

This validates that you can:
1. Generate circuit with isolated component (no nets)
2. Verify 0 hierarchical labels and unconnected pins in netlist
3. Add net connection to one pin in Python
4. Regenerate → hierarchical label appears on that pin only
5. Verify other pins remain unconnected in netlist

This is common during early design when components are placed but not
yet electrically connected.

Workflow:
1. Generate with R1 completely isolated (no nets)
2. Verify 0 hierarchical labels in schematic
3. Export netlist, verify all R1 pins unconnected (unconnected-*)
4. Add Net("NET1") in Python connecting R1[1]
5. Regenerate
6. Validate:
   - Hierarchical label "NET1" appears on R1[1] only
   - R1[2] still has no label
   - Component position preserved
   - Netlist shows R1[1] in NET1, R1[2] unconnected
   - No spurious unconnected-* entries for labeled pins

Validation uses:
- kicad-sch-api for schematic structure
- Netlist comparison for electrical connectivity
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def parse_netlist(netlist_content):
    """Parse netlist content and extract net information.

    Returns dict: {net_name: [(ref, pin), ...]}
    """
    nets = {}

    # Find all net blocks
    node_pattern = r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)'

    # Split into net blocks
    net_blocks = re.split(r'\(net\s+\(code', netlist_content)

    for block in net_blocks:
        if '(name "' not in block:
            continue

        # Reconstruct the net line for parsing
        block = '(net (code' + block

        # Extract net name
        name_match = re.search(r'\(name\s+"([^"]+)"\)', block)
        if not name_match:
            continue

        net_name = name_match.group(1).strip('/')

        # Skip unconnected nets starting with 'unconnected-'
        if net_name.startswith('unconnected-'):
            continue

        # Extract all nodes in this net
        nodes = []
        for node_match in re.finditer(node_pattern, block):
            ref = node_match.group(1)
            pin = node_match.group(2)
            nodes.append((ref, pin))

        if nodes:
            nets[net_name] = sorted(nodes)

    return nets


def get_unconnected_pins(netlist_content):
    """Extract unconnected pins from netlist.

    Returns list: [(ref, pin), ...]
    """
    unconnected = []

    # Find all unconnected-* nets
    node_pattern = r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)'

    # Split into net blocks
    net_blocks = re.split(r'\(net\s+\(code', netlist_content)

    for block in net_blocks:
        if '(name "' not in block:
            continue

        # Extract net name
        name_match = re.search(r'\(name\s+"([^"]+)"\)', block)
        if not name_match:
            continue

        net_name = name_match.group(1).strip('/')

        # Only process unconnected nets
        if not net_name.startswith('unconnected-'):
            continue

        # Extract all nodes in this net
        for node_match in re.finditer(node_pattern, block):
            ref = node_match.group(1)
            pin = node_match.group(2)
            unconnected.append((ref, pin))

    return sorted(unconnected)


def test_31_isolated_component(request):
    """Test handling of isolated components with no net connections.

    CRITICAL EARLY-STAGE WORKFLOW:
    Validates that isolated components (not yet electrically connected) are
    correctly handled with no spurious labels or net entries.

    This is THE workflow for early circuit design:
    - Start with components placed but not connected
    - Review layout in KiCad
    - Add connections incrementally
    - Regenerate - only connected pins get labels, isolated pins stay isolated

    Workflow:
    1. Generate with isolated R1 (no nets)
    2. Verify 0 hierarchical labels and all pins unconnected
    3. Add Net("NET1") to R1[1] only
    4. Regenerate → NET1 label on R1[1], R1[2] still isolated
    5. Validate netlist shows correct connectivity

    Level 3 Electrical Validation:
    - kicad-sch-api for schematic structure
    - Netlist comparison for isolated vs connected pins
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "isolated_resistor.py"
    output_dir = test_dir / "isolated_resistor"
    schematic_file = output_dir / "isolated_resistor.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file (unconnected)
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate with isolated component (no labels, no nets)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate isolated R1 (no net connections)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "isolated_resistor.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 1 failed: Initial generation\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Schematic not created"

        # Validate 1 component
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 1
        r1 = components[0]
        assert r1.reference == "R1"

        # Store initial position
        r1_initial_pos = r1.position

        # Verify NO hierarchical labels (component is isolated)
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        hierarchical_labels = sch_content.count('hierarchical_label')

        print(f"✅ Step 1: Isolated component generated")
        print(f"   - Component: R1 (10k)")
        print(f"   - Position: {r1_initial_pos}")
        print(f"   - Hierarchical labels: {hierarchical_labels} (should be 0)")

        assert hierarchical_labels == 0, (
            f"Expected no hierarchical labels for isolated component, "
            f"found {hierarchical_labels}"
        )

        # =====================================================================
        # STEP 2: Export initial netlist and verify all pins unconnected
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Export netlist and verify all pins unconnected")
        print("="*70)

        kicad_netlist_file_initial = output_dir / "isolated_resistor_initial.net"

        result = subprocess.run(
            [
                "kicad-cli", "sch", "export", "netlist",
                str(schematic_file),
                "--output", str(kicad_netlist_file_initial)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"kicad-cli netlist export failed\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Parse netlist
        with open(kicad_netlist_file_initial, 'r') as f:
            initial_netlist_content = f.read()

        nets_initial = parse_netlist(initial_netlist_content)
        unconnected_initial = get_unconnected_pins(initial_netlist_content)

        print(f"\n📊 Initial netlist:")
        print(f"   Named nets: {list(nets_initial.keys())}")
        print(f"   Unconnected pins: {unconnected_initial}")

        # Verify R1[1] and R1[2] are unconnected
        expected_unconnected = [("R1", "1"), ("R1", "2")]
        assert sorted(unconnected_initial) == sorted(expected_unconnected), (
            f"Expected R1[1] and R1[2] unconnected!\n"
            f"Expected: {sorted(expected_unconnected)}\n"
            f"Got: {sorted(unconnected_initial)}"
        )

        print(f"✅ Step 2: All R1 pins unconnected (as expected)")

        # =====================================================================
        # STEP 3: Add Net("NET1") to R1[1] in Python
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Add Net(\"NET1\") to R1[1] in Python")
        print("="*70)

        # Uncomment the net connection in Python code
        modified_code = original_code.replace(
            '# Note: uncomment to connect pin 1\n'
            '    # net1 = Net("NET1")\n'
            '    # r1[1] += net1',
            '# Connect pin 1\n'
            '    net1 = Net("NET1")\n'
            '    r1[1] += net1'
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 3: Net(\"NET1\") added to R1[1]")
        print(f"   - R1[1] now connected")
        print(f"   - R1[2] remains isolated")

        # =====================================================================
        # STEP 4: Regenerate with partial connection
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Regenerate with NET1 connection on R1[1]")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "isolated_resistor.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration with net\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # =====================================================================
        # STEP 5: Validate NET1 label on R1[1] only, R1[2] still isolated
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate NET1 label on R1[1], R1[2] isolated")
        print("="*70)

        sch_final = Schematic.load(str(schematic_file))
        components_final = sch_final.components

        assert len(components_final) == 1

        r1_final = components_final[0]
        r1_final_pos = r1_final.position

        # Validate position preserved
        assert r1_final_pos == r1_initial_pos, (
            f"R1 position changed!\n"
            f"Initial: {r1_initial_pos}\n"
            f"Final: {r1_final_pos}"
        )

        # Validate hierarchical label appeared on pin 1 only
        with open(schematic_file, 'r') as f:
            sch_content_final = f.read()

        net1_labels = sch_content_final.count('hierarchical_label "NET1"')

        assert net1_labels == 1, (
            f"Expected exactly 1 NET1 hierarchical label (on R1[1]), found {net1_labels}"
        )

        print(f"✅ Step 5: NET1 label on R1[1] only")
        print(f"   - NET1 labels: {net1_labels}")
        print(f"   - R1 position preserved: {r1_final_pos}")

        # =====================================================================
        # STEP 6: Export final netlist and validate connectivity
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Validate netlist - R1[1] connected, R1[2] isolated")
        print("="*70)

        kicad_netlist_file_final = output_dir / "isolated_resistor_final.net"

        result = subprocess.run(
            [
                "kicad-cli", "sch", "export", "netlist",
                str(schematic_file),
                "--output", str(kicad_netlist_file_final)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"kicad-cli netlist export failed\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Parse final netlist
        with open(kicad_netlist_file_final, 'r') as f:
            final_netlist_content = f.read()

        nets_final = parse_netlist(final_netlist_content)
        unconnected_final = get_unconnected_pins(final_netlist_content)

        print(f"\n📊 Final netlist:")
        print(f"   Named nets: {list(nets_final.keys())}")
        print(f"   Unconnected pins: {unconnected_final}")

        # Validate NET1 exists and connects R1[1]
        assert "NET1" in nets_final, (
            f"NET1 not found in final netlist! Found: {list(nets_final.keys())}"
        )

        net1_nodes = nets_final["NET1"]
        assert net1_nodes == [("R1", "1")], (
            f"NET1 should connect only R1[1]!\n"
            f"Expected: [('R1', '1')]\n"
            f"Got: {net1_nodes}"
        )

        # Validate R1[2] is still unconnected
        assert ("R1", "2") in unconnected_final, (
            f"R1[2] should remain unconnected!\n"
            f"Unconnected pins: {unconnected_final}"
        )

        # Validate R1[1] is NOT in unconnected list (it's in NET1)
        assert ("R1", "1") not in unconnected_final, (
            f"R1[1] should be in NET1, not unconnected!\n"
            f"Unconnected pins: {unconnected_final}"
        )

        print(f"\n✅ Step 6: Electrical connectivity VALIDATED!")
        print(f"   - NET1 connects: {net1_nodes}")
        print(f"   - R1[1] → NET1 ✓")
        print(f"   - R1[2] → unconnected ✓")
        print(f"\n🎉 Isolated component workflow works!")
        print(f"   Added partial connection without affecting other pins!")

    finally:
        # Restore original Python file (unconnected)
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

