#!/usr/bin/env python3
"""
Automated test for 33_bus_connections bidirectional test.

Tests CRITICAL real-world pattern: 8-bit data bus connecting multiple devices.

This validates that you can:
1. Generate circuit with 8-bit data bus (D0-D7)
2. All 8 nets created and connected properly
3. Modify a single bus line in Python
4. Regenerate → only modified line changes
5. Other bus lines unaffected

This is essential for microcontroller and digital logic circuit development.

Workflow:
1. Generate with MCU and MEM connected via 8-bit bus (D0-D7)
2. Verify 8 separate nets in netlist with correct connections
3. Modify one bus line (D0) to use different device
4. Regenerate
5. Validate:
   - D0 now has different connections
   - D1-D7 still have original connections
   - All nets present and valid
   - Netlist comparison confirms modification

Validation uses:
- kicad-sch-api for schematic structure
- Netlist parsing for connection verification
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


def test_33_bus_connections(request):
    """Test 8-bit data bus connection and modification.

    CRITICAL REAL-WORLD PATTERN:
    Validates that microcontroller circuits with data buses work correctly:
    - 8 separate nets (D0-D7) for data lines
    - Multiple devices (MCU, MEM) share bus lines
    - Can modify individual bus lines without affecting others

    This workflow is essential for:
    - Microcontroller design (MCU ↔ Memory data bus)
    - Digital logic circuits (address/data buses)
    - Iterative bus routing and pin assignment

    Workflow:
    1. Generate with 8-bit bus (D0-D7) connecting MCU and MEM
    2. Verify all 8 nets exist in schematic and netlist
    3. Verify each net has exactly 2 nodes (MCU and MEM)
    4. Modify D0 to use different device (buffer instead of MEM)
    5. Regenerate
    6. Validate:
       - D0 now connects MCU and BUF instead of MCU and MEM
       - D1-D7 still connect MCU and MEM
       - All 8 nets still present
       - Electrical connectivity via netlist verified

    Level 3 Electrical Validation:
    - kicad-sch-api for schematic structure
    - Netlist parsing for bus connectivity
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "eight_bit_bus.py"
    output_dir = test_dir / "eight_bit_bus"
    schematic_file = output_dir / "eight_bit_bus.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file (unmodified bus)
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate with 8-bit bus (D0-D7)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate with 8-bit data bus (D0-D7)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "eight_bit_bus.py"],
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

        # Validate components
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) >= 2, (
            f"Expected at least 2 components (MCU1, MEM1), "
            f"found {len(components)}"
        )

        refs = {c.reference for c in components}
        assert "MCU1" in refs, "MCU1 not found in schematic"
        assert "MEM1" in refs, "MEM1 not found in schematic"

        print(f"✅ Step 1: Initial circuit generated")
        print(f"   - Components: {sorted(refs)}")

        # =====================================================================
        # STEP 2: Verify 8-bit bus exists in schematic
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Verify 8-bit bus in schematic (D0-D7 labels)")
        print("="*70)

        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        # Check for hierarchical labels for each bus line
        bus_nets = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7"]
        found_labels = {}

        for bus_net in bus_nets:
            label_count = sch_content.count(f'hierarchical_label "{bus_net}"')
            found_labels[bus_net] = label_count

        print(f"   Hierarchical labels found:")
        for bus_net in bus_nets:
            count = found_labels[bus_net]
            status = "✓" if count >= 2 else "✗"
            print(f"   {status} {bus_net}: {count} labels (expected ≥2)")

        # Verify all 8 bus lines have at least 2 labels (MCU and MEM)
        for bus_net in bus_nets:
            assert found_labels[bus_net] >= 2, (
                f"{bus_net} missing hierarchical labels! "
                f"Expected ≥2, found {found_labels[bus_net]}"
            )

        print(f"\n✅ Step 2: All 8 bus lines verified with labels")

        # =====================================================================
        # STEP 3: Export and validate initial netlist
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Export and validate initial netlist")
        print("="*70)

        kicad_netlist_file = output_dir / "eight_bit_bus_kicad_initial.net"

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
            initial_netlist_content = f.read()

        initial_nets = parse_netlist(initial_netlist_content)

        print(f"\n📊 Initial netlist:")
        print(f"   Nets found: {sorted(initial_nets.keys())}")
        for bus_net in bus_nets:
            if bus_net in initial_nets:
                nodes = initial_nets[bus_net]
                print(f"   - {bus_net}: {nodes}")
            else:
                print(f"   - {bus_net}: NOT FOUND IN NETLIST")

        # Verify all 8 bus nets exist
        for bus_net in bus_nets:
            assert bus_net in initial_nets, (
                f"{bus_net} not found in initial netlist! "
                f"Found nets: {list(initial_nets.keys())}"
            )

        # Verify each bus line connects MCU and MEM (2 nodes each)
        for bus_net in bus_nets:
            nodes = initial_nets[bus_net]
            assert len(nodes) == 2, (
                f"{bus_net} has {len(nodes)} nodes, expected 2 (MCU and MEM)"
            )

            # Extract component references
            refs_in_net = {ref for ref, pin in nodes}
            assert "MCU1" in refs_in_net, f"{bus_net} missing MCU1"
            assert "MEM1" in refs_in_net, f"{bus_net} missing MEM1"

        print(f"\n✅ Step 3: Initial netlist validated")
        print(f"   - All 8 nets present (D0-D7)")
        print(f"   - Each net has 2 nodes (MCU1 and MEM1)")
        print(f"   - All bus lines connected correctly")

        # =====================================================================
        # STEP 4: Modify D0 bus line to use different device
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Modify D0 bus line (disconnect MEM, connect BUF)")
        print("="*70)

        # Modify Python code to change D0 connection
        # Remove MEM connection from D0, add BUF connection instead
        modified_code = original_code.replace(
            '    # D0 - Data bit 0\n'
            '    d0_net = Net(name="D0")\n'
            '    d0_net += mcu[1]  # MCU pin 1 → D0\n'
            '    d0_net += mem[1]  # MEM pin 1 → D0',
            '    # D0 - Data bit 0 (MODIFIED: using buffer instead of MEM)\n'
            '    d0_net = Net(name="D0")\n'
            '    d0_net += mcu[1]  # MCU pin 1 → D0\n'
            '    d0_net += buf[1]  # BUF pin 1 → D0 (changed from MEM)'
        )

        # Verify modification made
        assert modified_code != original_code, (
            "Modification code failed - original unchanged"
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 4: Python code modified")
        print(f"   - D0 now connects: MCU1[1] + BUF1[1] (was MCU1[1] + MEM1[1])")
        print(f"   - Other bus lines unchanged")

        # =====================================================================
        # STEP 5: Regenerate with modified bus
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Regenerate circuit with modified D0")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "eight_bit_bus.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 5 failed: Regeneration with modified bus\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 5: Circuit regenerated successfully")

        # =====================================================================
        # STEP 6: Validate modified netlist
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Validate modified netlist")
        print("="*70)

        kicad_netlist_file_modified = output_dir / "eight_bit_bus_kicad_modified.net"

        result = subprocess.run(
            [
                "kicad-cli", "sch", "export", "netlist",
                str(schematic_file),
                "--output", str(kicad_netlist_file_modified)
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

        with open(kicad_netlist_file_modified, 'r') as f:
            modified_netlist_content = f.read()

        modified_nets = parse_netlist(modified_netlist_content)

        print(f"\n📊 Modified netlist:")
        print(f"   Nets found: {sorted(modified_nets.keys())}")

        # =====================================================================
        # STEP 7: Compare before and after
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 7: Compare initial vs modified netlists")
        print("="*70)

        # All 8 nets should still exist
        for bus_net in bus_nets:
            assert bus_net in modified_nets, (
                f"{bus_net} disappeared from netlist after modification!"
            )

        print(f"\n✅ All 8 bus nets still present")

        # D0 should have CHANGED
        d0_initial = sorted(initial_nets["D0"])
        d0_modified = sorted(modified_nets["D0"])

        print(f"\n📊 D0 Bus Line Comparison:")
        print(f"   Initial:  {d0_initial}")
        print(f"   Modified: {d0_modified}")

        assert d0_initial != d0_modified, (
            f"D0 connection unchanged! Expected modification to be visible"
        )

        # Verify D0 now connects MCU1 and BUF1 (not MEM1)
        d0_refs = {ref for ref, pin in d0_modified}
        assert "MCU1" in d0_refs, "D0 missing MCU1"
        assert "BUF1" in d0_refs, "D0 missing BUF1 (should have been added)"
        assert "MEM1" not in d0_refs, "D0 still connected to MEM1 (should have been removed)"

        print(f"   ✅ D0 now connects: MCU1 ↔ BUF1 (correct!)")

        # D1-D7 should be UNCHANGED
        print(f"\n📊 Other Bus Lines (D1-D7) Comparison:")
        all_unchanged = True

        for bus_net in bus_nets[1:]:  # D1 through D7
            initial = sorted(initial_nets[bus_net])
            modified = sorted(modified_nets[bus_net])

            if initial == modified:
                print(f"   ✅ {bus_net}: {initial} (unchanged)")
            else:
                print(f"   ✗ {bus_net}: {initial} → {modified} (CHANGED!)")
                all_unchanged = False

        assert all_unchanged, (
            "Some bus lines (D1-D7) were modified when they shouldn't have been"
        )

        # =====================================================================
        # STEP 8: Final validation
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 8: Final validation summary")
        print("="*70)

        print(f"\n✅ Bus Connection Test PASSED!")
        print(f"\n📋 Summary:")
        print(f"   - Initial: 8 nets (D0-D7), each with 2 nodes (MCU1 + MEM1)")
        print(f"   - Modified: 8 nets (D0-D7), D0 now has MCU1 + BUF1")
        print(f"   - D1-D7: Unchanged (still MCU1 + MEM1)")
        print(f"   - All bus lines independently modifiable ✓")
        print(f"\n🎉 Real-world bus design pattern validated!")
        print(f"   Microcontroller buses work correctly!")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
