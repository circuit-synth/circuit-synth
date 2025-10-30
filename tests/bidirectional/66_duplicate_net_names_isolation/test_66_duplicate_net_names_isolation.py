#!/usr/bin/env python3
"""
Automated test for 66_duplicate_net_names_isolation.

Tests CRITICAL safety property: net namespace isolation between circuits.

This validates that:
1. Each @circuit function has isolated net namespace
2. Net("SIGNAL") in circuit_a ≠ Net("SIGNAL") in circuit_b
3. Components only connect within their own circuit
4. No implicit global nets - prevents dangerous accidental connections

Workflow:
1. Define circuit_a with Net("SIGNAL") connecting R1—R2
2. Define circuit_b with Net("SIGNAL") connecting R3—R4 (SAME NAME, different instance)
3. Main circuit instantiates both: circuit_a() and circuit_b()
4. Generate KiCad
5. Validate via netlist:
   - R1—R2 on one net (circuit_a's SIGNAL)
   - R3—R4 on different net (circuit_b's SIGNAL)
   - R1 NOT connected to R3 (nets are isolated)

This is a SAFETY test - if it fails, circuits can accidentally short together!

Level 3 Validation:
- Netlist comparison to prove nets are separate
- R1—R2 on one net, R3—R4 on different net
- No electrical connection between the two SIGNAL nets
"""
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


def test_66_duplicate_net_names_isolation(request):
    """Test that duplicate net names in different circuits remain isolated.

    CRITICAL SAFETY TEST:
    Validates net namespace isolation - same net name in different @circuit
    functions should create separate nets, NOT connect components across circuits.

    This prevents dangerous accidental connections:
    - circuit_a has Net("SIGNAL") connecting R1—R2
    - circuit_b has Net("SIGNAL") connecting R3—R4
    - These should be SEPARATE nets, not the same net

    If this test FAILS: Unrelated circuits could accidentally short together!

    Workflow:
    1. circuit_a: Net("SIGNAL") connects R1[1]—R2[1]
    2. circuit_b: Net("SIGNAL") connects R3[1]—R4[1] (SAME NAME)
    3. main() calls both circuit_a() and circuit_b()
    4. Generate KiCad
    5. Validate netlist:
       - R1 and R2 on one net
       - R3 and R4 on different net
       - R1 NOT connected to R3

    Level 3 Validation:
    - Netlist comparison proves nets are isolated
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "isolated_circuits.py"
    output_dir = test_dir / "isolated_circuits"
    schematic_file = output_dir / "isolated_circuits.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        # =====================================================================
        # STEP 1: Generate circuits with duplicate net names
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate circuits with duplicate Net(\"SIGNAL\") names")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "isolated_circuits.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 1 failed: Generation\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Schematic not created"

        # Validate 4 components exist
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 4, f"Expected 4 components, found {len(components)}"
        refs = {c.reference for c in components}
        assert refs == {"R1", "R2", "R3", "R4"}, f"Expected R1-R4, found {refs}"

        print(f"✅ Step 1: 4 components generated")
        print(f"   - Components: {sorted(refs)}")

        # =====================================================================
        # STEP 2: Export netlist and validate net isolation
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Validate net isolation via netlist")
        print("="*70)

        # Export netlist
        netlist_file = output_dir / "isolated_circuits.net"

        result = subprocess.run(
            [
                "kicad-cli", "sch", "export", "netlist",
                str(schematic_file),
                "--output", str(netlist_file)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Netlist export failed\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Parse netlist
        with open(netlist_file, 'r') as f:
            netlist_content = f.read()

        nets = parse_netlist(netlist_content)

        print(f"\n📊 Netlist analysis:")
        print(f"   Nets found: {list(nets.keys())}")
        for net_name, nodes in nets.items():
            print(f"   - {net_name}: {nodes}")

        # =====================================================================
        # STEP 3: Validate R1—R2 on one net, R3—R4 on different net
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Validate net isolation (CRITICAL SAFETY CHECK)")
        print("="*70)

        # Find which nets R1 and R3 are on
        r1_net = None
        r3_net = None

        for net_name, nodes in nets.items():
            node_refs = [ref for ref, pin in nodes]
            if "R1" in node_refs:
                r1_net = net_name
            if "R3" in node_refs:
                r3_net = net_name

        assert r1_net is not None, "R1 not found in any net"
        assert r3_net is not None, "R3 not found in any net"

        # CRITICAL: R1 and R3 must be on DIFFERENT nets
        assert r1_net != r3_net, (
            f"❌ SAFETY VIOLATION!\n"
            f"   R1 and R3 are on the SAME net: {r1_net}\n"
            f"   circuit_a's Net(\"SIGNAL\") and circuit_b's Net(\"SIGNAL\") merged!\n"
            f"   This is a dangerous bug - unrelated circuits connected!\n"
            f"\n"
            f"   Expected:\n"
            f"     - circuit_a: Net(\"SIGNAL\") connects R1—R2 only\n"
            f"     - circuit_b: Net(\"SIGNAL\") connects R3—R4 only\n"
            f"     - Separate net instances despite same name\n"
            f"\n"
            f"   Actual:\n"
            f"     - Both circuits merged into one net\n"
            f"     - Net namespace isolation BROKEN"
        )

        # Validate R1—R2 on same net
        r1_nodes = nets[r1_net]
        r1_refs = {ref for ref, pin in r1_nodes}

        assert "R1" in r1_refs and "R2" in r1_refs, (
            f"R1 and R2 should be on same net!\n"
            f"   Net {r1_net}: {r1_refs}"
        )

        # Validate R3—R4 on same net
        r3_nodes = nets[r3_net]
        r3_refs = {ref for ref, pin in r3_nodes}

        assert "R3" in r3_refs and "R4" in r3_refs, (
            f"R3 and R4 should be on same net!\n"
            f"   Net {r3_net}: {r3_refs}"
        )

        print(f"\n✅ Step 3: Net isolation VALIDATED!")
        print(f"   - circuit_a net ({r1_net}): {sorted(r1_refs)}")
        print(f"   - circuit_b net ({r3_net}): {sorted(r3_refs)}")
        print(f"   - Nets are SEPARATE ✓")
        print(f"   - No accidental connection between circuits ✓")
        print(f"\n🎉 SAFETY TEST PASSED!")
        print(f"   Net namespace isolation working correctly!")
        print(f"   Duplicate net names in different circuits remain isolated!")

    finally:
        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
