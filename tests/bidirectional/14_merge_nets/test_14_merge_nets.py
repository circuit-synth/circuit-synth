#!/usr/bin/env python3
"""
Automated test for 14_merge_nets bidirectional test.

Tests CRITICAL iterative development workflow: merging two separate nets
into one by connecting components across net boundaries.

This validates that you can:
1. Generate circuit with two separate nets (NET1: R1-R2, NET2: R3-R4)
2. Merge them by moving R3 and R4 to NET1 in Python
3. Regenerate → hierarchical labels update for all components
4. Component positions preserved (not reset)

This is a foundational workflow for circuit evolution and topology changes.

Workflow:
1. Generate with R1-R2 on NET1, R3-R4 on NET2 (two separate nets)
2. Verify netlist shows 2 separate nets
3. Merge all four onto NET1 in Python
4. Regenerate
5. Validate:
   - All four have NET1 labels
   - NET2 labels are gone
   - Single electrical net in netlist
   - Component positions preserved

Validation uses:
- kicad-sch-api for schematic structure
- Netlist comparison for electrical connectivity (Level 3)
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

        # Skip unconnected nets
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


@pytest.mark.xfail(
    reason="Issue #380: Synchronizer does not remove old hierarchical labels when nets are merged, "
           "resulting in old NET2 labels remaining after merge to NET1"
)
def test_14_merge_nets(request):
    """Test merging two separate nets into one.

    CRITICAL ITERATIVE WORKFLOW:
    Validates that you can merge nets by moving components from one net
    to another and regenerating without losing layout.

    This is a key workflow for circuit evolution:
    - Start with components on separate nets
    - Realize they should be connected
    - Move to same net in Python
    - Regenerate → labels update, layout preserved

    Workflow:
    1. Generate with R1-R2 on NET1, R3-R4 on NET2 (two nets)
    2. Verify two separate nets in schematic and netlist
    3. Merge all four onto NET1 in Python
    4. Regenerate → all get NET1 labels, NET2 removed
    5. Verify single electrical net in netlist

    Level 3 Electrical Validation:
    - kicad-sch-api for schematic structure
    - Netlist comparison for electrical connectivity
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "four_resistors.py"
    output_dir = test_dir / "four_resistors"
    schematic_file = output_dir / "four_resistors.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file (two separate nets)
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate with two separate nets (NET1: R1-R2, NET2: R3-R4)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate with two separate nets")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "four_resistors.py"],
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

        # Validate 4 components
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 4
        refs = {c.reference for c in components}
        assert refs == {"R1", "R2", "R3", "R4"}

        # Store initial positions
        initial_positions = {}
        for c in components:
            initial_positions[c.reference] = c.position

        # Verify two separate nets with hierarchical labels
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        net1_labels = sch_content.count('hierarchical_label "NET1"')
        net2_labels = sch_content.count('hierarchical_label "NET2"')

        print(f"✅ Step 1: Two separate nets generated")
        print(f"   - Components: {sorted(refs)}")
        print(f"   - NET1 labels: {net1_labels} (R1, R2)")
        print(f"   - NET2 labels: {net2_labels} (R3, R4)")
        for ref in sorted(refs):
            print(f"   - {ref} position: {initial_positions[ref]}")

        assert net1_labels >= 2, (
            f"Expected at least 2 NET1 labels, found {net1_labels}"
        )
        assert net2_labels >= 2, (
            f"Expected at least 2 NET2 labels, found {net2_labels}"
        )

        # =====================================================================
        # STEP 2: Export initial netlist and verify two nets
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Verify initial netlist shows two separate nets")
        print("="*70)

        kicad_netlist_file_initial = output_dir / "four_resistors_initial.net"

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

        with open(kicad_netlist_file_initial, 'r') as f:
            netlist_initial = f.read()

        nets_initial = parse_netlist(netlist_initial)

        print(f"\n📊 Initial netlist:")
        print(f"   Nets found: {list(nets_initial.keys())}")
        for net_name, nodes in nets_initial.items():
            print(f"   - {net_name}: {nodes}")

        assert "NET1" in nets_initial, "NET1 not found in initial netlist"
        assert "NET2" in nets_initial, "NET2 not found in initial netlist"

        net1_nodes_initial = nets_initial["NET1"]
        net2_nodes_initial = nets_initial["NET2"]

        assert len(net1_nodes_initial) == 2, (
            f"NET1 should have 2 nodes (R1-R2), found {len(net1_nodes_initial)}"
        )
        assert len(net2_nodes_initial) == 2, (
            f"NET2 should have 2 nodes (R3-R4), found {len(net2_nodes_initial)}"
        )

        print(f"\n✅ Step 2: Two separate nets confirmed")
        print(f"   - NET1: {net1_nodes_initial} (R1-R2)")
        print(f"   - NET2: {net2_nodes_initial} (R3-R4)")

        # =====================================================================
        # STEP 3: Merge nets in Python (move R3 and R4 to NET1)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Merge nets in Python")
        print("="*70)

        # Replace the two separate nets with one merged net
        modified_code = original_code.replace(
            '    # Create two separate nets\n'
            '    net1 = Net(name="NET1")\n'
            '    net1 += r1[1]\n'
            '    net1 += r2[1]\n'
            '\n'
            '    net2 = Net(name="NET2")\n'
            '    net2 += r3[1]\n'
            '    net2 += r4[1]',
            '    # Create merged net (all four resistors on NET1)\n'
            '    net1 = Net(name="NET1")\n'
            '    net1 += r1[1]\n'
            '    net1 += r2[1]\n'
            '    net1 += r3[1]\n'
            '    net1 += r4[1]'
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 3: Nets merged in Python")
        print(f"   - All four resistors moved to NET1")
        print(f"   - NET2 deleted")

        # =====================================================================
        # STEP 4: Regenerate with merged nets
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Regenerate with merged nets")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "four_resistors.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration with merged nets\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # =====================================================================
        # STEP 5: Validate labels updated and NET2 gone
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate all labels show NET1, NET2 labels gone")
        print("="*70)

        sch_final = Schematic.load(str(schematic_file))
        components_final = sch_final.components

        assert len(components_final) == 4

        # Validate component positions preserved
        final_positions = {}
        for c in components_final:
            final_positions[c.reference] = c.position

        for ref in sorted(refs):
            assert final_positions[ref] == initial_positions[ref], (
                f"{ref} position changed!\n"
                f"Initial: {initial_positions[ref]}\n"
                f"Final: {final_positions[ref]}"
            )

        # Validate labels in schematic
        with open(schematic_file, 'r') as f:
            sch_content_final = f.read()

        net1_labels_final = sch_content_final.count('hierarchical_label "NET1"')
        net2_labels_final = sch_content_final.count('hierarchical_label "NET2"')

        print(f"✅ Step 5: Labels validated")
        print(f"   - NET1 labels: {net1_labels_final} (should be 4)")
        print(f"   - NET2 labels: {net2_labels_final} (should be 0)")
        for ref in sorted(refs):
            print(f"   - {ref} position preserved: {final_positions[ref]}")

        assert net1_labels_final >= 4, (
            f"Expected at least 4 NET1 labels (all four resistors), "
            f"found {net1_labels_final}"
        )
        assert net2_labels_final == 0, (
            f"Expected no NET2 labels (should be deleted), found {net2_labels_final}"
        )

        # =====================================================================
        # STEP 6: Export final netlist and verify single merged net
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Validate electrical connectivity (netlist)")
        print("="*70)

        kicad_netlist_file_final = output_dir / "four_resistors_final.net"

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

        with open(kicad_netlist_file_final, 'r') as f:
            netlist_final = f.read()

        nets_final = parse_netlist(netlist_final)

        print(f"\n📊 Final netlist after merge:")
        print(f"   Nets found: {list(nets_final.keys())}")
        for net_name, nodes in nets_final.items():
            print(f"   - {net_name}: {nodes}")

        # Validate NET1 exists with all four resistors
        assert "NET1" in nets_final, "NET1 not found in final netlist"
        assert "NET2" not in nets_final, (
            f"NET2 should not exist after merge, but found in netlist"
        )

        net1_nodes_final = nets_final["NET1"]

        expected_nodes = [("R1", "1"), ("R2", "1"), ("R3", "1"), ("R4", "1")]
        assert sorted(net1_nodes_final) == sorted(expected_nodes), (
            f"NET1 should connect all four resistors!\n"
            f"Expected: {sorted(expected_nodes)}\n"
            f"Got: {sorted(net1_nodes_final)}"
        )

        print(f"\n✅ Step 6: Electrical connectivity VALIDATED!")
        print(f"   - NET1 connects all four: {net1_nodes_final}")
        print(f"   - NET2 deleted ✓")
        print(f"   - R1-R2-R3-R4 all electrically connected ✓")

        # =====================================================================
        # FINAL: Summary
        # =====================================================================
        print("\n" + "="*70)
        print("🎉 NET MERGE WORKFLOW SUCCESSFUL!")
        print("="*70)
        print("✅ Merged two separate nets into one")
        print("✅ All labels updated correctly")
        print("✅ Component positions preserved")
        print("✅ Electrical connectivity maintained")
        print("✅ NET2 completely removed")
        print("\nCircuit evolution workflow works perfectly!")

    finally:
        # Restore original Python file (two separate nets)
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
