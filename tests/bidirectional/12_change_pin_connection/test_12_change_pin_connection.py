#!/usr/bin/env python3
"""
Automated test for 12_change_pin_connection bidirectional test.

Tests changing which pin a net connects to, validating pin-level
connection accuracy in bidirectional sync.

This validates:
1. Initial connection: R1[1] → NET1 ← R2[1]
2. Change in Python: R1[2] → NET1 ← R2[1] (move NET1 from R1 pin 1 to pin 2)
3. Regenerate KiCad
4. Verify correct behavior (only new pin connected)

Workflow:
1. Generate with NET1 connecting R1[1] to R2[1]
2. Verify netlist: NET1 connects (R1, pin 1) and (R2, pin 1)
3. Modify Python: Move NET1 from R1[1] to R1[2]
4. Regenerate KiCad
5. Validate:
   - NET1 connects (R1, pin 2) and (R2, pin 1) only
   - Old label on R1 pin 1 is correctly removed
   - Component positions preserved

Validation uses:
- kicad-cli netlist export for electrical connectivity
- kicad-sch-api for position preservation
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
        node_pattern = r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)'
        nodes = []
        for node_match in re.finditer(node_pattern, block):
            ref = node_match.group(1)
            pin = node_match.group(2)
            nodes.append((ref, pin))

        if nodes:
            nets[net_name] = sorted(nodes)

    return nets


def test_12_change_pin_connection(request):
    """Test changing pin connection in Python → KiCad sync.

    CRITICAL PIN-LEVEL VALIDATION:
    Validates that changing which pin a net connects to works correctly
    and is reflected accurately in KiCad schematic and netlist.

    This is essential for:
    - Pin assignment changes during design iteration
    - Component swaps that change pin configurations
    - Correcting wiring errors

    Workflow:
    1. Generate with NET1: R1[1] ← NET1 → R2[1]
    2. Verify netlist shows (R1, 1) and (R2, 1)
    3. Change Python: R1[2] ← NET1 → R2[1]
    4. Regenerate
    5. Verify netlist shows (R1, 2) and (R2, 1)
    6. Verify component positions preserved

    Level 3 Electrical Validation:
    - kicad-cli netlist export for connectivity
    - kicad-sch-api for positions
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "two_resistors_initial.py"
    output_dir = test_dir / "two_resistors_pin_test"
    schematic_file = output_dir / "two_resistors_pin_test.kicad_sch"

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
        # STEP 1: Generate with NET1 on R1[1] and R2[1]
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate with NET1: R1[1] ← NET1 → R2[1]")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "two_resistors_initial.py"],
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

        # Validate 2 components and store positions
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 2
        refs = {c.reference for c in components}
        assert "R1" in refs and "R2" in refs

        r1_initial = next(c for c in components if c.reference == "R1")
        r2_initial = next(c for c in components if c.reference == "R2")

        r1_initial_pos = r1_initial.position
        r2_initial_pos = r2_initial.position
        r1_initial_uuid = r1_initial.uuid
        r2_initial_uuid = r2_initial.uuid

        print(f"✅ Step 1: Initial circuit generated")
        print(f"   - Components: {refs}")
        print(f"   - R1 position: {r1_initial_pos}, UUID: {r1_initial_uuid}")
        print(f"   - R2 position: {r2_initial_pos}, UUID: {r2_initial_uuid}")

        # =====================================================================
        # STEP 2: Verify initial netlist: NET1 connects R1[1] to R2[1]
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Verify initial netlist connectivity")
        print("="*70)

        kicad_netlist_file = output_dir / "two_resistors_pin_test_initial.net"

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

        print(f"\n📊 Initial netlist:")
        for net_name, nodes in initial_nets.items():
            print(f"   - {net_name}: {nodes}")

        # Validate NET1 connects R1[1] and R2[1]
        assert "NET1" in initial_nets, (
            f"NET1 not found in netlist! Found: {list(initial_nets.keys())}"
        )

        expected_initial = [("R1", "1"), ("R2", "1")]
        assert sorted(initial_nets["NET1"]) == sorted(expected_initial), (
            f"Initial NET1 connections incorrect!\n"
            f"Expected: {sorted(expected_initial)}\n"
            f"Got: {sorted(initial_nets['NET1'])}"
        )

        print(f"✅ Step 2: Initial connectivity validated")
        print(f"   - NET1 connects: (R1, pin 1) ← NET1 → (R2, pin 1) ✓")

        # =====================================================================
        # STEP 3: Change pin connection in Python: R1[1] → R1[2]
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Change Python code: R1[2] ← NET1 → R2[1]")
        print("="*70)

        # Modify Python code: r1[1] → r1[2]
        modified_code = original_code.replace(
            "# Connect R1 pin 1 to R2 pin 1\n"
            "    net1 = Net(\"NET1\")\n"
            "    r1[1] += net1\n"
            "    r2[1] += net1",
            "# Connect R1 pin 2 to R2 pin 1 (changed from pin 1)\n"
            "    net1 = Net(\"NET1\")\n"
            "    r1[2] += net1  # Changed from r1[1]\n"
            "    r2[1] += net1"
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 3: Python code modified")
        print(f"   - Changed: r1[1] += net1 → r1[2] += net1")

        # =====================================================================
        # STEP 4: Regenerate KiCad with changed pin connection
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Regenerate KiCad with pin connection change")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "two_resistors_initial.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration with pin change\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 4: Regeneration complete")

        # =====================================================================
        # STEP 5: Validate netlist shows changed connection
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate netlist reflects pin change")
        print("="*70)

        kicad_netlist_final = output_dir / "two_resistors_pin_test_final.net"

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

        print(f"\n📊 Final netlist:")
        for net_name, nodes in final_nets.items():
            print(f"   - {net_name}: {nodes}")

        # Validate NET1 now connects R1[2] and R2[1]
        assert "NET1" in final_nets, (
            f"NET1 not found in final netlist! Found: {list(final_nets.keys())}"
        )

        expected_final = [("R1", "2"), ("R2", "1")]
        assert sorted(final_nets["NET1"]) == sorted(expected_final), (
            f"Final NET1 connections incorrect!\n"
            f"Expected: {sorted(expected_final)}\n"
            f"Got: {sorted(final_nets['NET1'])}"
        )

        print(f"✅ Step 5: Pin connection change validated!")
        print(f"   - Initial: (R1, pin 1) ← NET1 → (R2, pin 1)")
        print(f"   - Final:   (R1, pin 2) ← NET1 → (R2, pin 1) ✓")

        # =====================================================================
        # STEP 6: Validate component identity and positions preserved
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Validate component identity and positions preserved")
        print("="*70)

        sch_final = Schematic.load(str(schematic_file))
        components_final = sch_final.components

        assert len(components_final) == 2

        r1_final = next(c for c in components_final if c.reference == "R1")
        r2_final = next(c for c in components_final if c.reference == "R2")

        r1_final_pos = r1_final.position
        r2_final_pos = r2_final.position
        r1_final_uuid = r1_final.uuid
        r2_final_uuid = r2_final.uuid

        # UUIDs should be preserved (proving synchronizer was used, not regeneration)
        assert r1_final_uuid == r1_initial_uuid, (
            f"R1 UUID changed! This indicates regeneration instead of synchronization.\n"
            f"Initial UUID: {r1_initial_uuid}\n"
            f"Final UUID:   {r1_final_uuid}"
        )

        assert r2_final_uuid == r2_initial_uuid, (
            f"R2 UUID changed! This indicates regeneration instead of synchronization.\n"
            f"Initial UUID: {r2_initial_uuid}\n"
            f"Final UUID:   {r2_final_uuid}"
        )

        # Positions should be preserved
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

        print(f"✅ Step 6: Component identity and positions preserved")
        print(f"   - R1 UUID: {r1_final_uuid} (preserved) ✓")
        print(f"   - R2 UUID: {r2_final_uuid} (preserved) ✓")
        print(f"   - R1 position: {r1_final_pos} (preserved) ✓")
        print(f"   - R2 position: {r2_final_pos} (preserved) ✓")
        print(f"\n🎉 Pin connection change workflow validated!")
        print(f"   - Electrical connectivity changed correctly")
        print(f"   - Component UUIDs preserved (synchronizer used, not regeneration)")
        print(f"   - Component positions preserved")
        print(f"   - Pin-level accuracy confirmed")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
