#!/usr/bin/env python3
"""
Automated test for 17_add_ground_symbol bidirectional test.

Tests adding a GND ground symbol connection to a component pin, validating
that the connection is correctly reflected in the generated netlist.

**TEST PURPOSE:**
Validate that when a user adds `Net("GND")` connection to a component pin
in Python and regenerates, the KiCad netlist correctly shows that pin
connected to the GND net.

This is fundamental to circuit design - every circuit needs ground connections,
and these must be correctly synchronized between Python and KiCad.

**WORKFLOW:**
1. Generate initial circuit with R1 (no ground connection)
2. Verify initial netlist shows R1 pin 2 NOT in any net
3. Modify Python: add `r1[2] += Net("GND")`
4. Regenerate KiCad
5. Verify final netlist shows R1 pin 2 connected to GND net
6. Verify R1 position preserved

**VALIDATION STRATEGY (Level 3 - Electrical):**
- kicad-cli netlist export for electrical connectivity verification
- Netlist parsing to extract component-pin-net relationships
- kicad-sch-api for position preservation validation
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

    # Find all net blocks (handling quoted code values)
    # Pattern: (net (code "X") (name "NET_NAME") ... (node ...))
    net_pattern = r'\(net\s+\(code\s+"[^"]*"\)\s+\(name\s+"([^"]+)"\).*?\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)'

    for match in re.finditer(net_pattern, netlist_content, re.DOTALL):
        net_name = match.group(1).strip('/')
        ref = match.group(2)
        pin = match.group(3)

        # Skip unconnected nets (they show as "unconnected-XXXX")
        if net_name.startswith('unconnected-'):
            continue

        # Add to nets dict
        if net_name not in nets:
            nets[net_name] = []
        nets[net_name].append((ref, pin))

    # Sort nodes in each net for consistent comparison
    for net_name in nets:
        nets[net_name] = sorted(nets[net_name])

    return nets


def get_unconnected_pins(netlist_content):
    """Extract unconnected pin references from netlist.

    Returns list of (ref, pin) tuples for pins not connected to any net.
    """
    unconnected = []

    # Find all unconnected net entries
    # Pattern: (net (code "X") (name "unconnected-...") ... (node (ref "R1") (pin "1") ...))
    # Note: code value is quoted in the netlist
    unconnected_pattern = r'\(net\s+\(code\s+"[^"]*"\)\s+\(name\s+"unconnected-[^"]+"\).*?\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)'
    for match in re.finditer(unconnected_pattern, netlist_content, re.DOTALL):
        ref = match.group(1)
        pin = match.group(2)
        unconnected.append((ref, pin))

    return unconnected


def test_17_add_ground_symbol(request):
    """Test adding GND ground symbol connection in Python → KiCad sync.

    CRITICAL GROUND HANDLING VALIDATION:
    Validates that adding a GND net connection to a component pin works
    correctly and is reflected accurately in KiCad schematic and netlist.

    This is essential for:
    - Ground/return path connections
    - Power plane connections
    - Basic circuit functionality

    Workflow:
    1. Generate with R1 (no ground)
    2. Verify netlist shows R1 pin 2 unconnected
    3. Change Python: r1[2] += Net("GND")
    4. Regenerate
    5. Verify netlist shows R1 pin 2 connected to GND
    6. Verify component position preserved

    Level 3 Electrical Validation:
    - kicad-cli netlist export for connectivity
    - kicad-sch-api for positions
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "resistor_with_ground.py"
    output_dir = test_dir / "resistor_with_ground"
    schematic_file = output_dir / "resistor_with_ground.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate with R1 (no ground connection)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate initial circuit with R1 (no ground)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "resistor_with_ground.py"],
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

        # Validate component and store position
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 1, f"Expected 1 component, got {len(components)}"
        r1_initial = components[0]
        assert r1_initial.reference == "R1"

        r1_initial_pos = r1_initial.position

        print(f"✅ Step 1: Initial circuit generated")
        print(f"   - Component: R1")
        print(f"   - R1 position: {r1_initial_pos}")
        print(f"   - No ground connection yet")

        # =====================================================================
        # STEP 2: Verify initial netlist shows R1 pin 2 unconnected
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Verify initial netlist (R1 pin 2 unconnected)")
        print("="*70)

        kicad_netlist_file = output_dir / "resistor_with_ground_initial.net"

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

        with open(kicad_netlist_file, 'r') as f:
            initial_netlist = f.read()

        initial_nets = parse_netlist(initial_netlist)
        initial_unconnected = get_unconnected_pins(initial_netlist)

        print(f"\n📊 Initial netlist:")
        print(f"   Connected nets: {initial_nets}")
        print(f"   Unconnected pins: {initial_unconnected}")

        # Verify R1 pin 2 is unconnected initially
        assert any(ref == "R1" and pin == "2" for ref, pin in initial_unconnected), (
            f"R1 pin 2 should be unconnected initially!\n"
            f"Unconnected pins: {initial_unconnected}"
        )

        # Verify no GND net yet
        assert "GND" not in initial_nets, (
            f"GND net should not exist initially!\n"
            f"Nets found: {list(initial_nets.keys())}"
        )

        print(f"✅ Step 2: Initial state verified")
        print(f"   - R1 pin 2 is unconnected ✓")
        print(f"   - No GND net exists yet ✓")

        # =====================================================================
        # STEP 3: Modify Python to add ground connection: r1[2] += Net("GND")
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Modify Python code: uncomment GND connection")
        print("="*70)

        # Uncomment the GND connection lines
        modified_code = original_code.replace(
            "    # gnd = Net(name=\"GND\")\n"
            "    # gnd += r1[2]",
            "    gnd = Net(name=\"GND\")\n"
            "    gnd += r1[2]"
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 3: Python code modified")
        print(f"   - Uncommented: gnd = Net(name=\"GND\")")
        print(f"   - Uncommented: gnd += r1[2]")

        # =====================================================================
        # STEP 4: Regenerate KiCad with ground connection
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Regenerate KiCad with ground connection")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "resistor_with_ground.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration with ground connection\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 4: Regeneration complete")

        # =====================================================================
        # STEP 5: Validate netlist shows R1 pin 2 connected to GND
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate netlist shows R1 pin 2 connected to GND")
        print("="*70)

        kicad_netlist_final = output_dir / "resistor_with_ground_final.net"

        result = subprocess.run(
            [
                "kicad-cli", "sch", "export", "netlist",
                str(schematic_file),
                "--output", str(kicad_netlist_final)
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

        with open(kicad_netlist_final, 'r') as f:
            final_netlist = f.read()

        final_nets = parse_netlist(final_netlist)
        final_unconnected = get_unconnected_pins(final_netlist)

        print(f"\n📊 Final netlist:")
        print(f"   Connected nets: {final_nets}")
        print(f"   Unconnected pins: {final_unconnected}")

        # Validate GND net exists and contains R1 pin 2
        assert "GND" in final_nets, (
            f"GND net should exist in final netlist!\n"
            f"Nets found: {list(final_nets.keys())}"
        )

        gnd_nodes = final_nets["GND"]
        print(f"\n   GND net connections: {gnd_nodes}")

        # R1 pin 2 should be in GND net
        assert ("R1", "2") in gnd_nodes, (
            f"R1 pin 2 should be connected to GND net!\n"
            f"GND net contains: {gnd_nodes}"
        )

        # R1 pin 2 should NOT be in unconnected list
        assert not any(ref == "R1" and pin == "2" for ref, pin in final_unconnected), (
            f"R1 pin 2 should NOT be unconnected after adding GND!\n"
            f"Unconnected pins: {final_unconnected}"
        )

        print(f"✅ Step 5: Ground connection validated!")
        print(f"   - GND net exists ✓")
        print(f"   - R1 pin 2 is in GND net ✓")
        print(f"   - R1 pin 2 is no longer unconnected ✓")

        # =====================================================================
        # STEP 6: Validate component position preserved & power symbol added
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Validate component position preserved & power symbol added")
        print("="*70)

        sch_final = Schematic.load(str(schematic_file))
        components_final = sch_final.components

        # Should now have R1 + GND power symbol (2 components)
        assert len(components_final) == 2, f"Expected 2 components (R1 + GND power symbol), got {len(components_final)}"

        # Find R1 and GND power symbol
        r1_final = None
        gnd_symbol = None
        for comp in components_final:
            if comp.reference == "R1":
                r1_final = comp
            elif comp.reference.startswith("#PWR"):
                gnd_symbol = comp

        assert r1_final is not None, "R1 component not found in final schematic"
        assert gnd_symbol is not None, "GND power symbol not found in final schematic"

        r1_final_pos = r1_final.position

        # Position should be preserved
        assert r1_final_pos == r1_initial_pos, (
            f"R1 position changed!\n"
            f"Initial: {r1_initial_pos}\n"
            f"Final: {r1_final_pos}"
        )

        print(f"✅ Step 6: Position preserved & power symbol added")
        print(f"   - R1 position: {r1_final_pos} ✓")
        print(f"   - GND power symbol: {gnd_symbol.reference} ✓")
        print(f"\n🎉 Ground symbol connection workflow validated!")
        print(f"   - Initial circuit generated (no ground)")
        print(f"   - Ground connection added in Python")
        print(f"   - Netlist correctly reflects GND connection")
        print(f"   - Component position preserved")
        print(f"   - GND power symbol automatically placed")
        print(f"   - Ground handling confirmed")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
