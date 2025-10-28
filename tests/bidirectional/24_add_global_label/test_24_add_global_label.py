#!/usr/bin/env python3
"""
Automated test for 24_add_global_label bidirectional test.

Tests CRITICAL iterative development workflow: adding electrical connections
to previously unconnected components using global labels.

This validates that you can:
1. Generate circuit with unconnected components
2. Add Net() in Python to connect them with global label scope
3. Regenerate → global labels appear, establishing electrical connection
4. Component positions preserved (not reset)
5. Global labels enable future cross-sheet connections in hierarchical designs

This is a foundational workflow for hierarchical circuit development.

Workflow:
1. Generate with R1 and R2 unconnected (no labels)
2. Verify no global labels in schematic
3. Add Net("GLOBAL_NET") in Python connecting R1[1] to R2[1]
4. Regenerate
5. Validate:
   - Global labels "GLOBAL_NET" appear on both pins
   - Component positions preserved
   - Electrical connectivity via netlist comparison

Validation uses:
- kicad-sch-api for schematic structure
- Text search for "global_label" in schematic file
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
    import re

    nets = {}

    # Find all net blocks
    net_pattern = r'\(net\s+\(code\s+"[^"]+"\)\s+\(name\s+"([^"]+)"\)'
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


def test_24_add_global_label(request):
    """Test adding global label net connection to existing unconnected components.

    CRITICAL ITERATIVE WORKFLOW:
    Validates that you can add electrical connections (Net objects with global labels)
    to previously unconnected components without losing layout.

    This enables hierarchical circuit development:
    - Start with flat circuit using global labels
    - Later add hierarchical sheets with same global net names
    - Cross-sheet connections automatically established

    Workflow:
    1. Generate with unconnected R1 and R2 (no labels)
    2. Verify no global labels exist
    3. Add Net("GLOBAL_NET") connecting R1[1] to R2[1]
    4. Regenerate → labels appear, positions preserved

    Level 3 Electrical Validation:
    - kicad-sch-api for schematic structure
    - Text search for "global_label" in schematic file
    - Netlist comparison for electrical connectivity
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "two_resistors.py"
    output_dir = test_dir / "two_resistors"
    schematic_file = output_dir / "two_resistors.kicad_sch"

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
        # STEP 1: Generate with unconnected components (no labels)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate with R1 and R2 unconnected (no labels)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "two_resistors.py"],
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

        # Validate 2 components
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 2
        refs = {c.reference for c in components}
        assert "R1" in refs and "R2" in refs

        # Store initial positions
        r1_initial = next(c for c in components if c.reference == "R1")
        r2_initial = next(c for c in components if c.reference == "R2")

        r1_initial_pos = r1_initial.position
        r2_initial_pos = r2_initial.position

        # Verify NO global labels (components are unconnected)
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        global_labels = sch_content.count('global_label')

        print(f"✅ Step 1: Unconnected components generated")
        print(f"   - Components: {refs}")
        print(f"   - R1 position: {r1_initial_pos}")
        print(f"   - R2 position: {r2_initial_pos}")
        print(f"   - Global labels: {global_labels} (should be 0)")

        assert global_labels == 0, (
            f"Expected no global labels for unconnected components, "
            f"found {global_labels}"
        )

        # =====================================================================
        # STEP 2: Add Net("GLOBAL_NET") in Python connecting R1[1] to R2[1]
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Add Net(\"GLOBAL_NET\") in Python")
        print("="*70)

        # Uncomment the global net connection in Python code
        modified_code = original_code.replace(
            '    # Note: uncomment to connect the resistors with global label\n'
            '    # global_net = Net("GLOBAL_NET")\n'
            '    # r1[1] += global_net\n'
            '    # r2[1] += global_net',
            '    # Connect the resistors with global label\n'
            '    global_net = Net("GLOBAL_NET")\n'
            '    r1[1] += global_net\n'
            '    r2[1] += global_net'
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 2: Net(\"GLOBAL_NET\") added to Python code")
        print(f"   - Connects R1[1] to R2[1]")

        # =====================================================================
        # STEP 3: Regenerate with connection
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Regenerate with GLOBAL_NET connection")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "two_resistors.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 3 failed: Regeneration with net\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # =====================================================================
        # STEP 4: Validate global labels appeared and positions preserved
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Validate GLOBAL_NET labels appeared")
        print("="*70)

        sch_final = Schematic.load(str(schematic_file))
        components_final = sch_final.components

        assert len(components_final) == 2

        r1_final = next(c for c in components_final if c.reference == "R1")
        r2_final = next(c for c in components_final if c.reference == "R2")

        r1_final_pos = r1_final.position
        r2_final_pos = r2_final.position

        # Validate positions preserved
        assert r1_final_pos == r1_initial_pos, (
            f"R1 position changed!\n"
            f"Initial: {r1_initial_pos}\n"
            f"Final: {r1_final_pos}"
        )

        assert r2_final_pos == r2_initial_pos, (
            f"R2 position changed!\n"
            f"Initial: {r2_initial_pos}\n"
            f"Final: {r2_final_pos}"
        )

        # Validate global labels appeared
        with open(schematic_file, 'r') as f:
            sch_content_final = f.read()

        global_net_labels = sch_content_final.count('global_label "GLOBAL_NET"')

        assert global_net_labels >= 2, (
            f"Expected at least 2 GLOBAL_NET global labels, found {global_net_labels}"
        )

        print(f"✅ Step 4: GLOBAL_NET labels appeared")
        print(f"   - GLOBAL_NET labels: {global_net_labels}")
        print(f"   - R1 position preserved: {r1_final_pos}")
        print(f"   - R2 position preserved: {r2_final_pos}")

        # =====================================================================
        # STEP 5: Validate electrical connectivity via netlist
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate electrical connectivity (netlist)")
        print("="*70)

        # Export netlist using kicad-cli
        kicad_netlist_file = output_dir / "two_resistors_kicad.net"

        result = subprocess.run(
            [
                "kicad-cli", "sch", "export", "netlist",
                str(schematic_file),
                "--output", str(kicad_netlist_file)
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
        with open(kicad_netlist_file, 'r') as f:
            kicad_netlist_content = f.read()

        nets = parse_netlist(kicad_netlist_content)

        print(f"\n📊 KiCad-exported netlist:")
        print(f"   Nets found: {list(nets.keys())}")
        for net_name, nodes in nets.items():
            print(f"   - {net_name}: {nodes}")

        # Validate GLOBAL_NET exists and connects R1[1] to R2[1]
        assert "GLOBAL_NET" in nets, (
            f"GLOBAL_NET not found in netlist! Found: {list(nets.keys())}"
        )

        expected_nodes = [("R1", "1"), ("R2", "1")]
        global_net_nodes = nets["GLOBAL_NET"]

        assert sorted(global_net_nodes) == sorted(expected_nodes), (
            f"GLOBAL_NET connections incorrect!\n"
            f"Expected: {sorted(expected_nodes)}\n"
            f"Got: {sorted(global_net_nodes)}"
        )

        print(f"\n✅ Step 5: Electrical connectivity VALIDATED!")
        print(f"   - GLOBAL_NET connects: {global_net_nodes}")
        print(f"   - R1 pin 1 → R2 pin 1 ✓")
        print(f"\n🎉 Iterative development workflow works!")
        print(f"   Added global label connection without losing layout!")
        print(f"   Ready for hierarchical expansion (cross-sheet connectivity)!")

    finally:
        # Restore original Python file (unconnected)
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
