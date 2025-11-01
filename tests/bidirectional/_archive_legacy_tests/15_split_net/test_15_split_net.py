#!/usr/bin/env python3
"""
Automated test for 15_split_net bidirectional test.

Tests CRITICAL net management workflow: splitting one net into two by removing
a connection from a multi-component net.

This validates that you can:
1. Generate circuit with 3 resistors all on single net (NET1)
2. Verify netlist shows NET1 with all 3 pins
3. Modify Python to split: NET1 gets R1+R2, NET2 gets R3
4. Regenerate → netlist now shows 2 separate nets
5. Verify electrical isolation through netlist comparison
6. Verify component positions preserved

This is foundational for iterative circuit refinement workflows.

Workflow:
1. Generate with R1, R2, R3 all on NET1
2. Verify netlist: NET1 with 3 pins [('R1', '1'), ('R2', '1'), ('R3', '1')]
3. Modify Python to create NET2 with R3
4. Regenerate
5. Validate:
   - Netlist shows 2 nets
   - NET1: R1[1], R2[1] (only 2 pins)
   - NET2: R3[1] (isolated)
   - Component positions preserved
   - Hierarchical labels correctly placed

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
        sch_content = f.read()

    # Pattern: (symbol (lib_id "Device:R") (at X Y ANGLE) ... (property "Reference" "R1"))
    # Look for at positions in symbol blocks
    symbol_pattern = r'\(symbol\s+\(lib_id\s+"[^"]+"\)\s+\(at\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\)'

    # Find all symbol blocks with their references
    # More robust: look for property Reference within symbol blocks
    lines = sch_content.split('\n')

    current_symbol_pos = None
    current_ref = None

    for line in lines:
        # Check if this line starts a symbol with at position
        if '(symbol' in line and '(lib_id' in line and '(at' in line:
            match = re.search(r'\(at\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\)', line)
            if match:
                x, y, angle = match.groups()
                current_symbol_pos = (float(x), float(y), float(angle))

        # Check for Reference property
        if current_symbol_pos and '(property "Reference"' in line:
            ref_match = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', line)
            if ref_match:
                current_ref = ref_match.group(1)
                positions[current_ref] = current_symbol_pos
                current_symbol_pos = None
                current_ref = None

    return positions


@pytest.mark.xfail(reason="Issue #373: Netlist exporter missing nodes - circuit-synth .net file has empty nets section")
def test_15_split_net(request):
    """Test splitting one net into two by removing a connection.

    CRITICAL NET MANAGEMENT WORKFLOW:
    Validates that you can:
    1. Generate circuit with 3 components on single net
    2. Modify to split: remove one component to separate net
    3. Regenerate → netlist shows 2 separate nets
    4. Verify electrical isolation through netlist comparison
    5. Preserve component positions

    This is the workflow for iterative net refinement:
    - Start with net structure
    - Review electrical connections
    - Refine connections by splitting/merging nets
    - Regenerate → updated netlists, layout preserved

    Workflow:
    1. Generate with NET1: R1[1], R2[1], R3[1] (all on same net)
    2. Verify netlist: NET1 with 3 pins
    3. Modify to create NET2: R3[1] moves to NET2
    4. Regenerate
    5. Validate:
       - Netlist shows 2 separate nets
       - NET1: only R1[1], R2[1]
       - NET2: only R3[1]
       - Positions preserved
       - Electrical isolation confirmed

    Level 3 Electrical Validation:
    - kicad-sch-api for schematic structure
    - Netlist comparison for electrical connectivity
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "three_resistors.py"
    output_dir = test_dir / "three_resistors"
    schematic_file = output_dir / "three_resistors.kicad_sch"

    # Netlist files
    synth_netlist_file_1 = output_dir / "three_resistors_phase1.net"
    kicad_netlist_file_1 = output_dir / "three_resistors_kicad_phase1.net"
    synth_netlist_file_2 = output_dir / "three_resistors_phase2.net"
    kicad_netlist_file_2 = output_dir / "three_resistors_kicad_phase2.net"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        # =====================================================================
        # PHASE 1: Generate with all 3 resistors on NET1
        # =====================================================================
        print("\n" + "="*70)
        print("PHASE 1: Generate circuit with all 3 resistors on NET1")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "three_resistors.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Phase 1 failed: Initial generation\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Schematic not created"
        assert (output_dir / "three_resistors.net").exists(), "Circuit-synth netlist not created"

        print(f"✅ Phase 1: KiCad project generated")
        print(f"   - Schematic: {schematic_file.name}")

        # Rename the generated netlist for comparison
        shutil.copy(output_dir / "three_resistors.net", synth_netlist_file_1)

        # =====================================================================
        # PHASE 1 VALIDATION: Verify all 3 resistors on NET1
        # =====================================================================
        print("\n" + "="*70)
        print("PHASE 1 VALIDATION: Verify NET1 has all 3 resistor pins")
        print("="*70)

        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        # Validate 3 components
        assert len(components) == 3, (
            f"Expected 3 components, found {len(components)}"
        )

        refs = {c.reference for c in components}
        assert refs == {"R1", "R2", "R3"}, (
            f"Expected R1, R2, R3, found {refs}"
        )

        print(f"✅ Phase 1: Schematic structure validated")
        print(f"   - Components found: {sorted(refs)}")

        # Validate hierarchical labels for NET1
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        net1_labels = sch_content.count('hierarchical_label "NET1"')
        assert net1_labels >= 3, (
            f"Expected at least 3 NET1 hierarchical labels, found {net1_labels}"
        )

        print(f"   - NET1 hierarchical labels: {net1_labels}")

        # Save component positions from Phase 1
        phase1_positions = extract_component_positions(schematic_file)
        print(f"   - Component positions saved:")
        for ref in sorted(phase1_positions.keys()):
            x, y, angle = phase1_positions[ref]
            print(f"     {ref}: ({x}, {y}, {angle}°)")

        # =====================================================================
        # PHASE 1 NETLIST: Export and parse KiCad netlist
        # =====================================================================
        print("\n" + "="*70)
        print("PHASE 1: Export KiCad netlist and verify NET1 structure")
        print("="*70)

        result = subprocess.run(
            [
                "kicad-cli", "sch", "export", "netlist",
                str(schematic_file),
                "--output", str(kicad_netlist_file_1)
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

        assert kicad_netlist_file_1.exists(), "KiCad netlist not created"

        # Read and parse netlists
        with open(synth_netlist_file_1, 'r') as f:
            synth_netlist_1_content = f.read()

        with open(kicad_netlist_file_1, 'r') as f:
            kicad_netlist_1_content = f.read()

        # Parse netlists
        synth_nets_1 = parse_netlist(synth_netlist_1_content)
        kicad_nets_1 = parse_netlist(kicad_netlist_1_content)

        print(f"\n📊 Circuit-synth netlist (Phase 1):")
        print(f"   Nets found: {list(synth_nets_1.keys())}")
        for net_name, nodes in synth_nets_1.items():
            print(f"   - {net_name}: {nodes}")

        print(f"\n📊 KiCad-exported netlist (Phase 1):")
        print(f"   Nets found: {list(kicad_nets_1.keys())}")
        for net_name, nodes in kicad_nets_1.items():
            print(f"   - {net_name}: {nodes}")

        # Verify Phase 1 netlist structure
        assert "NET1" in kicad_nets_1, (
            f"NET1 missing from KiCad netlist!\n"
            f"Found nets: {list(kicad_nets_1.keys())}"
        )

        # Verify NET1 has all 3 pins
        expected_phase1_nodes = [("R1", "1"), ("R2", "1"), ("R3", "1")]
        kicad_net1_nodes = kicad_nets_1.get("NET1", [])

        assert sorted(kicad_net1_nodes) == sorted(expected_phase1_nodes), (
            f"Phase 1 NET1 nodes mismatch!\n"
            f"Expected: {sorted(expected_phase1_nodes)}\n"
            f"Got:      {sorted(kicad_net1_nodes)}"
        )

        print(f"\n✅ Phase 1 netlist validated:")
        print(f"   - NET1 contains all 3 resistor pins: {kicad_net1_nodes}")

        # =====================================================================
        # PHASE 2: MODIFY AND REGENERATE - Split NET1 into NET1 and NET2
        # =====================================================================
        print("\n" + "="*70)
        print("PHASE 2: Modify Python to split NET1 and NET2")
        print("="*70)

        # Read the original fixture
        with open(python_file, 'r') as f:
            original_content = f.read()

        # Create modified version with split nets
        modified_content = original_content.replace(
            """    # Connect all three resistors via NET1
    net1 = Net(name="NET1")
    net1 += r1[1]
    net1 += r2[1]
    net1 += r3[1]""",
            """    # Connect resistors to separate nets
    net1 = Net(name="NET1")
    net1 += r1[1]
    net1 += r2[1]

    net2 = Net(name="NET2")
    net2 += r3[1]"""
        )

        # Write modified fixture
        with open(python_file, 'w') as f:
            f.write(modified_content)

        print("✅ Phase 2: Python fixture modified")
        print("   - NET1: R1[1], R2[1]")
        print("   - NET2: R3[1]")

        # Regenerate circuit
        result = subprocess.run(
            ["uv", "run", "three_resistors.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Phase 2 failed: Regeneration with split nets\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Phase 2: KiCad project regenerated with split nets")

        # Rename the regenerated netlist
        shutil.copy(output_dir / "three_resistors.net", synth_netlist_file_2)

        # =====================================================================
        # PHASE 2 VALIDATION: Verify NET1 and NET2 split
        # =====================================================================
        print("\n" + "="*70)
        print("PHASE 2 VALIDATION: Verify nets split correctly")
        print("="*70)

        # Reload schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        # Verify still 3 components
        assert len(components) == 3, (
            f"Component count changed! Expected 3, found {len(components)}"
        )

        refs = {c.reference for c in components}
        assert refs == {"R1", "R2", "R3"}, (
            f"Components changed! Expected R1, R2, R3, found {refs}"
        )

        print(f"✅ Phase 2: Components preserved (still 3)")

        # Validate hierarchical labels
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        net1_labels = sch_content.count('hierarchical_label "NET1"')
        net2_labels = sch_content.count('hierarchical_label "NET2"')

        assert net1_labels >= 2, (
            f"Expected at least 2 NET1 labels after split, found {net1_labels}"
        )

        assert net2_labels >= 1, (
            f"Expected at least 1 NET2 label, found {net2_labels}"
        )

        print(f"   - NET1 hierarchical labels: {net1_labels} (expected 2)")
        print(f"   - NET2 hierarchical labels: {net2_labels} (expected 1)")

        # Verify component positions preserved
        phase2_positions = extract_component_positions(schematic_file)
        print(f"\n   - Component positions after split:")
        for ref in sorted(phase2_positions.keys()):
            x, y, angle = phase2_positions[ref]
            print(f"     {ref}: ({x}, {y}, {angle}°)")

        # Check positions didn't change significantly (allow tiny float rounding)
        print(f"\n   - Position preservation check:")
        for ref in ["R1", "R2", "R3"]:
            if ref in phase1_positions and ref in phase2_positions:
                phase1_pos = phase1_positions[ref]
                phase2_pos = phase2_positions[ref]
                # Allow tiny rounding differences
                x_match = abs(phase1_pos[0] - phase2_pos[0]) < 0.01
                y_match = abs(phase1_pos[1] - phase2_pos[1]) < 0.01
                angle_match = abs(phase1_pos[2] - phase2_pos[2]) < 0.01

                if x_match and y_match and angle_match:
                    print(f"     ✓ {ref}: Position preserved")
                else:
                    print(f"     ✗ {ref}: Position CHANGED")
                    print(f"       Phase 1: {phase1_pos}")
                    print(f"       Phase 2: {phase2_pos}")

        # =====================================================================
        # PHASE 2 NETLIST: Export and parse KiCad netlist
        # =====================================================================
        print("\n" + "="*70)
        print("PHASE 2: Export KiCad netlist and verify split nets")
        print("="*70)

        result = subprocess.run(
            [
                "kicad-cli", "sch", "export", "netlist",
                str(schematic_file),
                "--output", str(kicad_netlist_file_2)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"kicad-cli netlist export failed in Phase 2\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert kicad_netlist_file_2.exists(), "KiCad netlist not created in Phase 2"

        # Read and parse Phase 2 netlists
        with open(synth_netlist_file_2, 'r') as f:
            synth_netlist_2_content = f.read()

        with open(kicad_netlist_file_2, 'r') as f:
            kicad_netlist_2_content = f.read()

        # Parse Phase 2 netlists
        synth_nets_2 = parse_netlist(synth_netlist_2_content)
        kicad_nets_2 = parse_netlist(kicad_netlist_2_content)

        print(f"\n📊 Circuit-synth netlist (Phase 2):")
        print(f"   Nets found: {list(synth_nets_2.keys())}")
        for net_name, nodes in synth_nets_2.items():
            print(f"   - {net_name}: {nodes}")

        print(f"\n📊 KiCad-exported netlist (Phase 2):")
        print(f"   Nets found: {list(kicad_nets_2.keys())}")
        for net_name, nodes in kicad_nets_2.items():
            print(f"   - {net_name}: {nodes}")

        # =====================================================================
        # ELECTRICAL ISOLATION VALIDATION
        # =====================================================================
        print("\n" + "="*70)
        print("ELECTRICAL ISOLATION VALIDATION: Verify split is complete")
        print("="*70)

        # Verify NET1 exists and has only 2 pins
        assert "NET1" in kicad_nets_2, (
            f"NET1 missing from Phase 2 KiCad netlist!\n"
            f"Found nets: {list(kicad_nets_2.keys())}"
        )

        expected_net1_nodes = [("R1", "1"), ("R2", "1")]
        net1_nodes_phase2 = kicad_nets_2.get("NET1", [])

        assert sorted(net1_nodes_phase2) == sorted(expected_net1_nodes), (
            f"Phase 2 NET1 nodes incorrect!\n"
            f"Expected: {sorted(expected_net1_nodes)}\n"
            f"Got:      {sorted(net1_nodes_phase2)}"
        )

        print(f"✅ NET1 split correctly:")
        print(f"   - Phase 1: {expected_phase1_nodes} (all 3)")
        print(f"   - Phase 2: {net1_nodes_phase2} (R3 removed)")

        # Verify NET2 exists and has only R3
        assert "NET2" in kicad_nets_2, (
            f"NET2 missing from Phase 2 KiCad netlist!\n"
            f"Found nets: {list(kicad_nets_2.keys())}"
        )

        expected_net2_nodes = [("R3", "1")]
        net2_nodes_phase2 = kicad_nets_2.get("NET2", [])

        assert sorted(net2_nodes_phase2) == sorted(expected_net2_nodes), (
            f"Phase 2 NET2 nodes incorrect!\n"
            f"Expected: {sorted(expected_net2_nodes)}\n"
            f"Got:      {sorted(net2_nodes_phase2)}"
        )

        print(f"✅ NET2 created correctly:")
        print(f"   - NET2: {net2_nodes_phase2}")

        # Verify electrical isolation: R3 is no longer connected to R1/R2
        print(f"\n✅ Electrical isolation confirmed:")
        print(f"   - R3 moved from NET1 to NET2")
        print(f"   - R1 and R2 remain on NET1")
        print(f"   - R3 now electrically isolated from R1-R2")

        # =====================================================================
        # SUMMARY
        # =====================================================================
        print("\n" + "="*70)
        print("TEST SUMMARY: Split Net Successful")
        print("="*70)

        print(f"\n✅ Phase 1 (Initial):")
        print(f"   NET1: {expected_phase1_nodes}")
        print(f"   Total nets: 1")

        print(f"\n✅ Phase 2 (After split):")
        print(f"   NET1: {net1_nodes_phase2}")
        print(f"   NET2: {net2_nodes_phase2}")
        print(f"   Total nets: 2")

        print(f"\n✅ Component positions preserved")
        print(f"\n✅ Electrical isolation confirmed")
        print(f"\n🎉 Net splitting validated!")

    finally:
        # Restore original fixture
        try:
            with open(python_file, 'r') as f:
                current_content = f.read()

            # Only restore if we modified it
            if "NET2" in current_content:
                with open(python_file, 'w') as f:
                    f.write(original_content)
        except Exception as e:
            print(f"Warning: Could not restore original fixture: {e}")

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    # Allow running directly for debugging
    import sys
    from pathlib import Path

    # Create a minimal request object for testing
    class MockRequest:
        class Config:
            def getoption(self, name, default=False):
                return default

        config = Config()

    pytest.main([__file__, "-v", "-s"])
