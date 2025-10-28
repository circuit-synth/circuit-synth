#!/usr/bin/env python3
"""
Automated test for 27_add_junction bidirectional test.

Tests CRITICAL schematic topology validation: junction placement for T-connections
where multiple nets meet at one point.

This validates that you can:
1. Generate circuit with T-connection (3 resistors on one net) requiring junction
2. Verify junction exists at connection point (search for `(junction` in .kicad_sch)
3. Modify Python to create Y-connection (separate nets)
4. Regenerate → junction removed or count changes appropriately
5. Verify component positions preserved
6. Verify electrical connectivity preserved

This is foundational for clear schematic topology and ERC validation.

Workflow:
1. Generate with R1, R2, R3 all on NET1 (T-connection requiring junction)
2. Verify junction exists in schematic file
3. Modify Python to create NET2 with R3 (Y-connection, no junction needed)
4. Regenerate
5. Validate:
   - Junction removed/count decreased
   - Component positions preserved
   - Electrical connectivity maintained
   - Schematic structure valid

Validation uses:
- kicad-sch-api for schematic structure
- Text search for `(junction` elements in .kicad_sch
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def extract_junctions(schematic_file):
    """Extract junctions from schematic file.

    Returns list of junction objects with positions.

    KiCad junction format:
    (junction (at X Y) (diameter 0) ...)
    """
    junctions = []

    with open(schematic_file, 'r') as f:
        content = f.read()

    # Find all junction elements
    # Pattern: (junction (at X Y) ...)
    junction_pattern = r'\(junction\s+\(at\s+([0-9.]+)\s+([0-9.]+)\)'

    for match in re.finditer(junction_pattern, content):
        x = float(match.group(1))
        y = float(match.group(2))
        junctions.append({'x': x, 'y': y, 'pos': (x, y)})

    return junctions


def parse_netlist(netlist_content):
    """Parse netlist content and extract net information.

    Returns dict: {net_name: [(ref, pin), ...]}

    Example netlist format:
    (net (code "1") (name "/NET1")
      (node (ref "R1") (pin "1"))
      (node (ref "R2") (pin "1"))
      (node (ref "R3") (pin "1")))
    """
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


def extract_component_positions(schematic_file):
    """Extract component positions from schematic.

    Returns dict: {ref: (x, y), ...}
    """
    positions = {}

    with open(schematic_file, 'r') as f:
        content = f.read()

    # Find all symbol blocks and their positions
    # Pattern: (symbol (lib_id "...") ... (property "Reference" "R1" ...) ... (at X Y))
    # We need to find the component reference first, then its at position
    symbol_pattern = r'\(symbol\s+\(lib_id\s+"[^"]+"\).*?\(property\s+"Reference"\s+"([^"]+)"'
    at_pattern = r'\(at\s+([0-9.]+)\s+([0-9.]+)\)'

    # More robust approach: find each symbol and extract reference, then position
    symbol_blocks = re.finditer(
        r'\(symbol\s+\(lib_id\s+"[^"]+"\)[^)]*?\(property\s+"Reference"\s+"([^"]+)"[^)]*?\(at\s+([0-9.]+)\s+([0-9.]+)\)',
        content,
        re.DOTALL
    )

    for match in symbol_blocks:
        ref = match.group(1)
        x = float(match.group(2))
        y = float(match.group(3))
        positions[ref] = (x, y)

    return positions


def test_27_add_junction(request):
    """Test junction placement for T-connections.

    CRITICAL SCHEMATIC TOPOLOGY VALIDATION:
    Validates that junctions are correctly placed when multiple nets meet at
    one point (T-connections), and correctly removed when topology changes.

    This is THE validation for clear schematic topology:
    - T-connections (3+ wires at one point) require junctions
    - Y-connections (label-based nets) don't need junctions
    - KiCad must automatically manage junctions based on topology

    Workflow:
    1. Generate with T-connection requiring junction (NET1: R1, R2, R3)
    2. Verify junction exists at connection point
    3. Modify to Y-connection (NET1: R1, R2; NET2: R3)
    4. Regenerate → junction removed/count changes
    5. Validate positions preserved and connectivity maintained

    Level 2 Validation:
    - kicad-sch-api for schematic structure
    - Text search for `(junction` elements
    - netlist comparison for electrical connectivity
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "three_resistors.py"
    output_dir = test_dir / "three_resistors"
    schematic_file = output_dir / "three_resistors.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file (T-connection)
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate with T-connection requiring junction
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate with R1, R2, R3 in T-connection (junction needed)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "three_resistors.py"],
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

        # Validate 3 components
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 3, f"Expected 3 components, got {len(components)}"
        refs = {c.reference for c in components}
        assert "R1" in refs and "R2" in refs and "R3" in refs, f"Expected R1, R2, R3; got {refs}"

        # Store initial positions
        positions_initial = extract_component_positions(schematic_file)

        print(f"✅ Step 1: T-connection circuit generated")
        print(f"   - Components: {refs}")
        print(f"   - Positions: {positions_initial}")

        # =====================================================================
        # STEP 2: Verify junction exists at connection point
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Verify junction exists for T-connection")
        print("="*70)

        junctions_initial = extract_junctions(schematic_file)

        # For a T-connection, we expect at least 1 junction at the connection point
        assert len(junctions_initial) > 0, (
            f"Expected at least 1 junction for T-connection, found {len(junctions_initial)}"
        )

        print(f"✅ Step 2: Junction verified")
        print(f"   - Junctions found: {len(junctions_initial)}")
        for i, junction in enumerate(junctions_initial):
            print(f"     Junction {i+1}: ({junction['x']}, {junction['y']})")

        # Verify schematic contains junction elements
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        junction_count_text = sch_content.count('(junction')
        assert junction_count_text > 0, "No junction elements found in schematic file"
        print(f"   - Junction count (text search): {junction_count_text}")

        # =====================================================================
        # STEP 3: Export initial netlist
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Export initial netlist (T-connection)")
        print("="*70)

        kicad_netlist_file_initial = output_dir / "three_resistors_initial.net"

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

        # Parse initial netlist
        with open(kicad_netlist_file_initial, 'r') as f:
            initial_netlist_content = f.read()

        nets_initial = parse_netlist(initial_netlist_content)

        print(f"✅ Step 3: Initial netlist exported")
        print(f"   Nets found: {list(nets_initial.keys())}")
        for net_name, nodes in nets_initial.items():
            print(f"   - {net_name}: {nodes}")

        # Verify NET1 exists with all 3 components
        assert "NET1" in nets_initial, (
            f"NET1 not found in initial netlist! Found: {list(nets_initial.keys())}"
        )

        expected_nodes_initial = [("R1", "1"), ("R2", "1"), ("R3", "1")]
        net1_nodes_initial = nets_initial["NET1"]

        assert sorted(net1_nodes_initial) == sorted(expected_nodes_initial), (
            f"NET1 connections incorrect!\n"
            f"Expected: {sorted(expected_nodes_initial)}\n"
            f"Got: {sorted(net1_nodes_initial)}"
        )

        print(f"   - NET1 correctly connects R1[1], R2[1], R3[1]")

        # =====================================================================
        # STEP 4: Modify to Y-connection (separate nets)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Modify to Y-connection (NET1: R1-R2, NET2: R3)")
        print("="*70)

        # Change to Y-connection: split NET1 and NET2
        modified_code = original_code.replace(
            '    # T-connection: all three resistors connected via NET1\n'
            '    # This creates a three-way junction at one point requiring a junction dot\n'
            '    net1 = Net(name="NET1")\n'
            '    net1 += r1[1]\n'
            '    net1 += r2[1]\n'
            '    net1 += r3[1]',
            '    # Y-connection: NET1 connects R1 and R2, NET2 connects R3 separately\n'
            '    # No junction needed (connections are label-based, not physical wires)\n'
            '    net1 = Net(name="NET1")\n'
            '    net1 += r1[1]\n'
            '    net1 += r2[1]\n'
            '\n'
            '    net2 = Net(name="NET2")\n'
            '    net2 += r3[1]'
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 4: Python modified to Y-connection")
        print(f"   - NET1 now connects: R1[1], R2[1]")
        print(f"   - NET2 now connects: R3[1]")

        # =====================================================================
        # STEP 5: Regenerate with Y-connection
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Regenerate with Y-connection")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "three_resistors.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 5 failed: Regeneration with Y-connection\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 5: Regenerated with Y-connection")

        # =====================================================================
        # STEP 6: Verify junction removed or count changed
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Verify junction removed (Y-connection doesn't need junctions)")
        print("="*70)

        junctions_final = extract_junctions(schematic_file)

        # For a Y-connection (label-based), we expect 0 junctions
        print(f"   - Junctions after Y-connection: {len(junctions_final)}")

        # Junction count should be less than initial (or zero)
        # Allow some tolerance for label placement
        assert len(junctions_final) < len(junctions_initial), (
            f"Expected fewer junctions after Y-connection!\n"
            f"Initial: {len(junctions_initial)}, Final: {len(junctions_final)}"
        )

        print(f"   - Junction count decreased from {len(junctions_initial)} to {len(junctions_final)}")

        # Verify schematic junction count decreased
        with open(schematic_file, 'r') as f:
            sch_content_final = f.read()

        junction_count_final = sch_content_final.count('(junction')
        assert junction_count_final < junction_count_text, (
            f"Expected fewer junctions in final schematic!\n"
            f"Initial: {junction_count_text}, Final: {junction_count_final}"
        )

        print(f"   - Text search junction count: {junction_count_final} (was {junction_count_text})")

        # =====================================================================
        # STEP 7: Verify component positions preserved
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 7: Validate positions preserved")
        print("="*70)

        positions_final = extract_component_positions(schematic_file)

        for ref in positions_initial:
            initial_pos = positions_initial[ref]
            final_pos = positions_final.get(ref)

            assert final_pos is not None, f"Component {ref} missing in final schematic"

            # Allow small tolerance for rounding (0.01 unit)
            x_diff = abs(initial_pos[0] - final_pos[0])
            y_diff = abs(initial_pos[1] - final_pos[1])

            assert x_diff < 0.01 and y_diff < 0.01, (
                f"{ref} position changed!\n"
                f"Initial: {initial_pos}\n"
                f"Final: {final_pos}"
            )

        print(f"✅ Step 7: Positions preserved")
        print(f"   - R1: {positions_final.get('R1')}")
        print(f"   - R2: {positions_final.get('R2')}")
        print(f"   - R3: {positions_final.get('R3')}")

        # =====================================================================
        # STEP 8: Export and verify final netlist
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 8: Export and verify final netlist")
        print("="*70)

        kicad_netlist_file_final = output_dir / "three_resistors_final.net"

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

        print(f"✅ Step 8: Final netlist exported")
        print(f"   Nets found: {list(nets_final.keys())}")
        for net_name, nodes in nets_final.items():
            print(f"   - {net_name}: {nodes}")

        # Verify NET1 now has only R1 and R2
        assert "NET1" in nets_final, (
            f"NET1 not found in final netlist! Found: {list(nets_final.keys())}"
        )

        expected_net1_final = [("R1", "1"), ("R2", "1")]
        net1_final = nets_final["NET1"]

        assert sorted(net1_final) == sorted(expected_net1_final), (
            f"NET1 should only have R1[1] and R2[1]!\n"
            f"Expected: {sorted(expected_net1_final)}\n"
            f"Got: {sorted(net1_final)}"
        )

        # Verify NET2 exists with only R3
        assert "NET2" in nets_final, (
            f"NET2 not found in final netlist! Found: {list(nets_final.keys())}"
        )

        expected_net2_final = [("R3", "1")]
        net2_final = nets_final["NET2"]

        assert sorted(net2_final) == sorted(expected_net2_final), (
            f"NET2 should only have R3[1]!\n"
            f"Expected: {sorted(expected_net2_final)}\n"
            f"Got: {sorted(net2_final)}"
        )

        print(f"\n✅ All validations PASSED!")
        print(f"   - T-connection had junctions, Y-connection removed them")
        print(f"   - Component positions preserved")
        print(f"   - Electrical connectivity correct")
        print(f"\n🎉 Junction management works correctly!")

    finally:
        # Restore original Python file (T-connection)
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
