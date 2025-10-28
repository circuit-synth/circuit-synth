#!/usr/bin/env python3
"""
Automated test for 21_multi_unit_components bidirectional test.

Tests CRITICAL functionality: Multi-unit components (quad op-amps, dual gates, etc.)
maintain all units and correct pin mappings when regenerating from Python.

Core Question: When you have a quad op-amp with 4 units and regenerate, are all
4 units still present with correct pin connections?

Workflow:
1. Generate KiCad with quad op-amp (TL074) using all 4 units
2. Verify netlist shows all 4 units (U1A, U1B, U1C, U1D) with correct pins
3. Modify Python to change unit B output net
4. Regenerate KiCad project
5. Validate:
   - All 4 units still present in schematic
   - Unit B has updated connections (verified in netlist)
   - Units A, C, D connections preserved from initial generation
   - Multi-unit component integrity maintained

Validation uses netlist comparison (Level 3 electrical validation).
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

    # Split into net blocks to extract net names
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


def test_21_multi_unit_components(request):
    """Test multi-unit component preservation when regenerating.

    CRITICAL FUNCTIONALITY:
    Validates that multi-unit components (quad op-amps, dual gates, etc.)
    maintain all units and correct pin mappings when regenerating from Python.

    This is critical because:
    - Quad op-amps, dual gates, etc. are fundamental to real circuits
    - If units don't regenerate correctly, users must manually recreate them
    - This would make the tool unusable for complex circuits

    Workflow:
    1. Generate with quad op-amp using all 4 units
    2. Verify netlist shows all 4 units with correct pins
    3. Modify unit B output net
    4. Regenerate → Unit B should have updated net, others preserved
    5. Verify netlist shows all 4 units with correct mappings

    Level 3 Electrical Validation:
    - kicad-sch-api for schematic structure
    - Netlist comparison for multi-unit pin mappings
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "quad_opamp.py"
    output_dir = test_dir / "quad_opamp"
    schematic_file = output_dir / "quad_opamp.kicad_sch"

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
        # STEP 1: Generate KiCad with quad op-amp (all 4 units)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with quad op-amp (4 units)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "quad_opamp.py"],
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

        # Validate schematic structure
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        # Count components
        component_count = len(components)
        print(f"✅ Step 1: Quad op-amp generated")
        print(f"   - Total components: {component_count}")
        print(f"   - Components: {[c.reference for c in components[:5]]}...")

        # Verify U1 (quad op-amp) is present
        u1_component = next((c for c in components if c.reference == "U1"), None)
        assert u1_component is not None, "U1 (quad op-amp) not found"
        print(f"   - U1 symbol: {u1_component.symbol}")

        # =====================================================================
        # STEP 2: Generate and parse initial netlist
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Verify initial netlist (all 4 units with correct pins)")
        print("="*70)

        kicad_netlist_file = output_dir / "quad_opamp_initial.net"

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
            netlist_content = f.read()

        nets_initial = parse_netlist(netlist_content)

        print(f"✅ Step 2: Initial netlist parsed")
        print(f"   - Total nets: {len(nets_initial)}")

        # Verify each unit has connections
        unit_pins_expected = {
            'U1': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14']
        }

        u1_pins_in_netlist = set()
        for net_name, nodes in nets_initial.items():
            for ref, pin in nodes:
                if ref == "U1":
                    u1_pins_in_netlist.add(pin)

        print(f"   - U1 pins in netlist: {sorted(u1_pins_in_netlist)}")
        assert len(u1_pins_in_netlist) >= 12, (
            f"U1 should have at least 12 pins in netlist, found {len(u1_pins_in_netlist)}"
        )

        # Extract unit A, B, C, D related nets
        # Unit A: pins 1, 2, 3
        # Unit B: pins 5, 6, 7
        # Unit C: pins 8, 9, 10
        # Unit D: pins 12, 13, 14
        # Shared: pins 4, 11 (power)

        unit_a_nets = []
        unit_b_nets = []
        unit_c_nets = []
        unit_d_nets = []

        for net_name, nodes in nets_initial.items():
            for ref, pin in nodes:
                if ref == "U1":
                    if pin in ['1', '2', '3']:
                        unit_a_nets.append((net_name, pin))
                    elif pin in ['5', '6', '7']:
                        unit_b_nets.append((net_name, pin))
                    elif pin in ['8', '9', '10']:
                        unit_c_nets.append((net_name, pin))
                    elif pin in ['12', '13', '14']:
                        unit_d_nets.append((net_name, pin))

        print(f"   - Unit A nets: {unit_a_nets}")
        print(f"   - Unit B nets: {unit_b_nets}")
        print(f"   - Unit C nets: {unit_c_nets}")
        print(f"   - Unit D nets: {unit_d_nets}")

        assert len(unit_a_nets) >= 3, f"Unit A should have >= 3 pins, found {len(unit_a_nets)}"
        assert len(unit_b_nets) >= 3, f"Unit B should have >= 3 pins, found {len(unit_b_nets)}"
        assert len(unit_c_nets) >= 3, f"Unit C should have >= 3 pins, found {len(unit_c_nets)}"
        assert len(unit_d_nets) >= 3, f"Unit D should have >= 3 pins, found {len(unit_d_nets)}"

        # Store initial unit B nets for later comparison
        initial_unit_b_nets = set((net, pin) for net, pin in unit_b_nets)
        print(f"\n✅ Initial Unit B nets: {initial_unit_b_nets}")

        # =====================================================================
        # STEP 3: Modify Python to change unit B output net
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Modify unit B output net in Python")
        print("="*70)

        # Change OUT_B to OUT_B_MODIFIED
        modified_code = original_code.replace(
            'net_out_b = Net("OUT_B")',
            'net_out_b = Net("OUT_B_MODIFIED")'
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 3: Unit B output net changed")
        print(f"   - From: OUT_B")
        print(f"   - To: OUT_B_MODIFIED")

        # =====================================================================
        # STEP 4: Regenerate KiCad with modified unit B
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Regenerate KiCad with modified unit B")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "quad_opamp.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 4: Regenerated KiCad with modified unit B")

        # =====================================================================
        # STEP 5: Verify all 4 units still present and unit B updated
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate multi-unit component integrity")
        print("="*70)

        # Verify schematic still has U1
        sch_final = Schematic.load(str(schematic_file))
        components_final = sch_final.components

        u1_final = next((c for c in components_final if c.reference == "U1"), None)
        assert u1_final is not None, "U1 missing in regenerated schematic!"

        print(f"✅ U1 (quad op-amp) still present in regenerated schematic")

        # Generate new netlist
        kicad_netlist_file_modified = output_dir / "quad_opamp_modified.net"

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
            f"kicad-cli netlist export failed on modified schematic\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Parse modified netlist
        with open(kicad_netlist_file_modified, 'r') as f:
            netlist_content_modified = f.read()

        nets_modified = parse_netlist(netlist_content_modified)

        print(f"✅ Modified netlist parsed")
        print(f"   - Total nets: {len(nets_modified)}")

        # Verify all 4 units still have connections
        u1_pins_modified = set()
        for net_name, nodes in nets_modified.items():
            for ref, pin in nodes:
                if ref == "U1":
                    u1_pins_modified.add(pin)

        print(f"   - U1 pins in modified netlist: {sorted(u1_pins_modified)}")
        assert len(u1_pins_modified) >= 12, (
            f"U1 should still have >= 12 pins after regeneration, "
            f"found {len(u1_pins_modified)}"
        )

        # Extract modified unit nets
        unit_a_nets_mod = []
        unit_b_nets_mod = []
        unit_c_nets_mod = []
        unit_d_nets_mod = []

        for net_name, nodes in nets_modified.items():
            for ref, pin in nodes:
                if ref == "U1":
                    if pin in ['1', '2', '3']:
                        unit_a_nets_mod.append((net_name, pin))
                    elif pin in ['5', '6', '7']:
                        unit_b_nets_mod.append((net_name, pin))
                    elif pin in ['8', '9', '10']:
                        unit_c_nets_mod.append((net_name, pin))
                    elif pin in ['12', '13', '14']:
                        unit_d_nets_mod.append((net_name, pin))

        print(f"   - Unit A nets (modified): {unit_a_nets_mod}")
        print(f"   - Unit B nets (modified): {unit_b_nets_mod}")
        print(f"   - Unit C nets (modified): {unit_c_nets_mod}")
        print(f"   - Unit D nets (modified): {unit_d_nets_mod}")

        # =====================================================================
        # CRITICAL VALIDATIONS
        # =====================================================================
        print("\n" + "="*70)
        print("CRITICAL VALIDATIONS: Multi-Unit Component Integrity")
        print("="*70)

        # 1. All 4 units still present
        assert len(unit_a_nets_mod) >= 3, "Unit A missing!"
        assert len(unit_b_nets_mod) >= 3, "Unit B missing!"
        assert len(unit_c_nets_mod) >= 3, "Unit C missing!"
        assert len(unit_d_nets_mod) >= 3, "Unit D missing!"
        print("✅ All 4 units still present")

        # 2. Unit B output net changed
        modified_unit_b_nets = set((net, pin) for net, pin in unit_b_nets_mod)

        # Unit B pin 7 is the output - it should be on OUT_B_MODIFIED now
        unit_b_pin_7_nets = [net for net, pin in unit_b_nets_mod if pin == '7']
        assert len(unit_b_pin_7_nets) > 0, "Unit B pin 7 (output) not found!"

        # Check if OUT_B_MODIFIED is in the nets
        has_modified_output = any('OUT_B_MODIFIED' in net for net in unit_b_pin_7_nets)
        assert has_modified_output, (
            f"Unit B output (pin 7) should be on OUT_B_MODIFIED, "
            f"but found: {unit_b_pin_7_nets}"
        )
        print(f"✅ Unit B output net changed to OUT_B_MODIFIED")

        # 3. Units A, C, D preserved
        initial_unit_a = set((net, pin) for net, pin in unit_a_nets)
        initial_unit_c = set((net, pin) for net, pin in unit_c_nets)
        initial_unit_d = set((net, pin) for net, pin in unit_d_nets)

        modified_unit_a = set((net, pin) for net, pin in unit_a_nets_mod)
        modified_unit_c = set((net, pin) for net, pin in unit_c_nets_mod)
        modified_unit_d = set((net, pin) for net, pin in unit_d_nets_mod)

        # Units A, C, D should be unchanged (same nets for same pins)
        assert modified_unit_a == initial_unit_a, (
            f"Unit A nets changed!\n"
            f"Initial: {initial_unit_a}\n"
            f"Modified: {modified_unit_a}"
        )
        print(f"✅ Unit A preserved (unchanged)")

        assert modified_unit_c == initial_unit_c, (
            f"Unit C nets changed!\n"
            f"Initial: {initial_unit_c}\n"
            f"Modified: {modified_unit_c}"
        )
        print(f"✅ Unit C preserved (unchanged)")

        assert modified_unit_d == initial_unit_d, (
            f"Unit D nets changed!\n"
            f"Initial: {initial_unit_d}\n"
            f"Modified: {modified_unit_d}"
        )
        print(f"✅ Unit D preserved (unchanged)")

        # =====================================================================
        # FINAL SUMMARY
        # =====================================================================
        print("\n" + "="*70)
        print("🎉 MULTI-UNIT COMPONENT INTEGRITY VERIFIED!")
        print("="*70)
        print(f"✅ All 4 units present in initial generation")
        print(f"✅ All 4 units present after regeneration")
        print(f"✅ Unit B connections updated as expected")
        print(f"✅ Units A, C, D preserved unchanged")
        print(f"✅ Multi-unit component functionality working correctly")
        print(f"\nThis test validates that multi-unit components (quad op-amps,")
        print(f"dual gates, etc.) are production-ready and maintain their")
        print(f"integrity when regenerating from Python code.")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
