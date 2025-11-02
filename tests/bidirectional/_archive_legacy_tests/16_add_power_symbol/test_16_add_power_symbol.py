#!/usr/bin/env python3
"""
Automated test for 16_add_power_symbol bidirectional test.

Tests CRITICAL iterative development workflow: adding power connections
to previously unconnected components.

This validates that you can:
1. Generate circuit with unconnected component (R1)
2. Add VCC Net() in Python to connect power
3. Regenerate → hierarchical label appears, establishing power connection
4. Component position preserved (not reset)
5. Netlist validates electrical connectivity (Level 3)

This is a foundational workflow for power management in circuits.

Workflow:
1. Generate with R1 unconnected (no labels)
2. Verify no hierarchical labels in schematic
3. Add Net("VCC") in Python connecting R1[1] to power
4. Regenerate
5. Validate:
   - Hierarchical label "VCC" appears on R1[1]
   - Component position preserved
   - Electrical connectivity via netlist comparison
   - Power net recognized (global connection semantics)

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


def test_16_add_power_symbol(request):
    """Test adding power symbol (VCC net) connection to existing unconnected component.

    CRITICAL ITERATIVE WORKFLOW:
    Validates that you can add power connections (Net objects) to
    previously unconnected components without losing layout.

    This is THE workflow for power management:
    - Start with component structure only (R1)
    - Review layout in KiCad
    - Add power connections in Python (VCC, GND nets)
    - Regenerate → connections appear, layout preserved

    Power nets have special handling:
    - VCC is a known power net name
    - Generates hierarchical label with global semantics
    - All VCC references connect globally (standard circuit semantics)
    - Netlist validation confirms electrical connectivity

    Workflow:
    1. Generate with unconnected R1 (no labels)
    2. Verify no hierarchical labels exist
    3. Add Net("VCC") connecting R1[1] to power
    4. Regenerate → label appears, position preserved

    Level 3 Electrical Validation:
    - kicad-sch-api for schematic structure
    - Netlist comparison for electrical connectivity
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "resistor_with_power.py"
    output_dir = test_dir / "resistor_with_power"
    schematic_file = output_dir / "resistor_with_power.kicad_sch"

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
        # STEP 1: Generate with unconnected component (no labels)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate with R1 unconnected (no power labels)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "resistor_with_power.py"],
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

        # Validate component exists
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 1
        r1 = components[0]
        assert r1.reference == "R1"

        # Store initial position
        r1_initial_pos = r1.position

        # Verify NO hierarchical labels (component is unconnected)
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        hierarchical_labels = sch_content.count('hierarchical_label')

        print(f"✅ Step 1: Unconnected component generated")
        print(f"   - Component: R1")
        print(f"   - R1 position: {r1_initial_pos}")
        print(f"   - Hierarchical labels: {hierarchical_labels} (should be 0)")

        assert hierarchical_labels == 0, (
            f"Expected no hierarchical labels for unconnected component, "
            f"found {hierarchical_labels}"
        )

        # =====================================================================
        # STEP 2: Add VCC Net in Python connecting R1[1] to power
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Add VCC Net() in Python")
        print("="*70)

        # Uncomment the VCC net connection in Python code
        modified_code = original_code.replace(
            '# Note: uncomment to add power connection\n'
            '    # vcc = Net(name="VCC")\n'
            '    # vcc += r1[1]',
            '# Add power connection\n'
            '    vcc = Net(name="VCC")\n'
            '    vcc += r1[1]'
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 2: VCC Net() added to Python code")
        print(f"   - Connects R1[1] to VCC power rail")

        # =====================================================================
        # STEP 3: Regenerate with power connection
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Regenerate with VCC power connection")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "resistor_with_power.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 3 failed: Regeneration with VCC net\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # =====================================================================
        # STEP 4: Validate VCC label appeared and position preserved
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Validate VCC label appeared")
        print("="*70)

        sch_final = Schematic.load(str(schematic_file))
        components_final = sch_final.components

        # Should now have R1 + VCC power symbol (2 components)
        assert len(components_final) == 2, f"Expected 2 components (R1 + VCC power symbol), got {len(components_final)}"

        # Find R1 and VCC power symbol
        r1_final = None
        vcc_symbol = None
        for comp in components_final:
            if comp.reference == "R1":
                r1_final = comp
            elif comp.reference.startswith("#PWR"):
                vcc_symbol = comp

        assert r1_final is not None, "R1 component not found in final schematic"
        assert vcc_symbol is not None, "VCC power symbol not found in final schematic"

        r1_final_pos = r1_final.position

        # Validate position preserved
        assert r1_final_pos == r1_initial_pos, (
            f"R1 position changed!\n"
            f"Initial: {r1_initial_pos}\n"
            f"Final: {r1_final_pos}"
        )

        print(f"✅ Step 4: VCC power symbol appeared")
        print(f"   - VCC power symbol: {vcc_symbol.reference}")
        print(f"   - R1 position preserved: {r1_final_pos}")
        print(f"   Note: Power symbols replace hierarchical labels")

        # =====================================================================
        # STEP 5: Validate electrical connectivity via netlist
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate electrical connectivity (netlist)")
        print("="*70)

        # Export netlist using kicad-cli
        kicad_netlist_file = output_dir / "resistor_with_power_kicad.net"

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

        # Validate VCC exists and connects R1[1]
        assert "VCC" in nets, (
            f"VCC net not found in netlist! Found: {list(nets.keys())}"
        )

        vcc_nodes = nets["VCC"]
        expected_nodes = [("R1", "1")]

        assert ("R1", "1") in vcc_nodes, (
            f"R1 pin 1 not connected to VCC!\n"
            f"VCC connections: {vcc_nodes}\n"
            f"Expected: {expected_nodes}"
        )

        print(f"\n✅ Step 5: Electrical connectivity VALIDATED!")
        print(f"   - VCC connects: {vcc_nodes}")
        print(f"   - R1 pin 1 → VCC ✓")
        print(f"\n🎉 Power connection workflow works!")
        print(f"   Added VCC connection without losing layout!")

    finally:
        # Restore original Python file (unconnected)
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
