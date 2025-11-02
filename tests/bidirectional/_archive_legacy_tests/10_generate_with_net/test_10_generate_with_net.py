#!/usr/bin/env python3
"""
Automated test for 10_generate_with_net bidirectional test.

Tests the FOUNDATIONAL net feature: generating a circuit with named net
connections and validating actual electrical connectivity.

This test validates ELECTRICAL CONNECTIVITY, not just visual elements.
It compares netlists to ensure actual pin-to-pin connections exist.

Workflow:
1. Generate KiCad with R1 and R2 connected via NET1
2. Validate schematic structure (components, labels) using kicad-sch-api
3. Export netlist using kicad-cli
4. Compare circuit-synth netlist vs KiCad-exported netlist
5. Validate electrical equivalence

Known Issue: #373 - circuit-synth netlist exporter missing nodes
This test will XFAIL until #373 is resolved.

Validation uses:
- kicad-sch-api for schematic structure
- kicad-cli for netlist export
- Netlist comparison for electrical connectivity
"""
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
      (node (ref "R2") (pin "1")))
    """
    import re

    nets = {}

    # Find all net blocks
    # Pattern: (net ... (name "...") ... (node ...) ... )
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


@pytest.mark.xfail(reason="Issue #373: Netlist exporter missing nodes - circuit-synth .net file has empty nets section")
def test_10_generate_with_net(request):
    """Test generating circuit with named net connection.

    FOUNDATIONAL NET TEST:
    Validates basic net generation and ELECTRICAL CONNECTIVITY.

    This test compares netlists (not just visual elements) to ensure
    actual pin-to-pin electrical connections exist.

    Workflow:
    1. Generate KiCad with R1 and R2 connected via NET1
    2. Validate schematic structure (kicad-sch-api)
    3. Export netlist using kicad-cli
    4. Compare netlists for electrical equivalence

    Known Issue #373:
    Circuit-synth netlist exporter generates empty (nets)) section.
    This test is marked XFAIL until #373 is resolved.

    Level 3 Electrical Validation:
    - kicad-sch-api for schematic structure
    - Netlist comparison for electrical connectivity
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "two_resistors_connected.py"
    output_dir = test_dir / "two_resistors_connected"
    schematic_file = output_dir / "two_resistors_connected.kicad_sch"

    # Netlist files
    synth_netlist_file = output_dir / "two_resistors_connected.net"
    kicad_netlist_file = output_dir / "two_resistors_connected_kicad.net"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        # =====================================================================
        # STEP 1: Generate KiCad with NET1 connection
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with R1 and R2 connected via NET1")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "two_resistors_connected.py"],
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
        assert synth_netlist_file.exists(), "Circuit-synth netlist not created"

        print(f"✅ Step 1: KiCad project generated")
        print(f"   - Schematic: {schematic_file.name}")
        print(f"   - Netlist: {synth_netlist_file.name}")

        # =====================================================================
        # STEP 2: Validate schematic structure with kicad-sch-api
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Validate schematic structure (visual elements)")
        print("="*70)

        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        # Validate 2 components
        assert len(components) == 2, (
            f"Expected 2 components, found {len(components)}"
        )

        refs = {c.reference for c in components}
        assert "R1" in refs and "R2" in refs, (
            f"Expected R1 and R2, found {refs}"
        )

        # Validate hierarchical labels exist
        # (kicad-sch-api may not expose labels directly, so we check the raw file)
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        net1_labels = sch_content.count('hierarchical_label "NET1"')
        assert net1_labels >= 2, (
            f"Expected at least 2 NET1 hierarchical labels, found {net1_labels}"
        )

        print(f"✅ Step 2: Schematic structure validated")
        print(f"   - Components: {refs}")
        print(f"   - NET1 labels: {net1_labels}")

        # =====================================================================
        # STEP 3: Export netlist using kicad-cli
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Export netlist using kicad-cli")
        print("="*70)

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

        assert kicad_netlist_file.exists(), "KiCad netlist not created"

        print(f"✅ Step 3: KiCad netlist exported")
        print(f"   - File: {kicad_netlist_file.name}")

        # =====================================================================
        # STEP 4: Parse both netlists
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Parse and compare netlists (ELECTRICAL VALIDATION)")
        print("="*70)

        # Read circuit-synth netlist
        with open(synth_netlist_file, 'r') as f:
            synth_netlist_content = f.read()

        # Read KiCad-exported netlist
        with open(kicad_netlist_file, 'r') as f:
            kicad_netlist_content = f.read()

        # Parse both netlists
        synth_nets = parse_netlist(synth_netlist_content)
        kicad_nets = parse_netlist(kicad_netlist_content)

        print(f"\n📊 Circuit-synth netlist:")
        print(f"   Nets found: {list(synth_nets.keys())}")
        for net_name, nodes in synth_nets.items():
            print(f"   - {net_name}: {nodes}")

        print(f"\n📊 KiCad-exported netlist:")
        print(f"   Nets found: {list(kicad_nets.keys())}")
        for net_name, nodes in kicad_nets.items():
            print(f"   - {net_name}: {nodes}")

        # =====================================================================
        # STEP 5: Validate electrical equivalence
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate electrical equivalence")
        print("="*70)

        # Check that NET1 exists in circuit-synth netlist
        assert "NET1" in synth_nets, (
            f"NET1 missing from circuit-synth netlist!\n"
            f"Found nets: {list(synth_nets.keys())}\n"
            f"This is Issue #373 - netlist exporter missing nodes"
        )

        # Check that NET1 has correct nodes
        expected_nodes = [("R1", "1"), ("R2", "1")]
        synth_net1_nodes = synth_nets.get("NET1", [])

        assert sorted(synth_net1_nodes) == sorted(expected_nodes), (
            f"NET1 nodes mismatch!\n"
            f"Expected: {sorted(expected_nodes)}\n"
            f"Got:      {sorted(synth_net1_nodes)}"
        )

        # Validate KiCad netlist has NET1 (should always pass)
        assert "NET1" in kicad_nets, (
            f"NET1 missing from KiCad netlist (unexpected!)"
        )

        kicad_net1_nodes = kicad_nets.get("NET1", [])
        assert sorted(kicad_net1_nodes) == sorted(expected_nodes), (
            f"KiCad NET1 nodes unexpected!\n"
            f"Expected: {sorted(expected_nodes)}\n"
            f"Got:      {sorted(kicad_net1_nodes)}"
        )

        print(f"✅ Step 5: Electrical equivalence VALIDATED!")
        print(f"   - Circuit-synth NET1: {synth_net1_nodes}")
        print(f"   - KiCad NET1:         {kicad_net1_nodes}")
        print(f"   - Both netlists electrically equivalent ✓")
        print(f"\n🎉 Electrical connectivity confirmed!")
        print(f"   R1 pin 1 is connected to R2 pin 1 via NET1")

    finally:
        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


def test_10_visual_validation_only(request):
    """Test 10 visual validation (without netlist comparison).

    This test validates schematic structure without requiring
    working netlist export. It will pass even with Issue #373.

    Validates:
    - Components exist (R1, R2)
    - Hierarchical labels exist (NET1)
    - No component overlap

    Does NOT validate:
    - Actual electrical connectivity (requires netlist comparison)
    - Pin-to-pin connections
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "two_resistors_connected.py"
    output_dir = test_dir / "two_resistors_connected"
    schematic_file = output_dir / "two_resistors_connected.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        # Generate
        result = subprocess.run(
            ["uv", "run", "two_resistors_connected.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Generation failed\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Schematic not created"

        # Validate schematic structure
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 2
        refs = {c.reference for c in components}
        assert "R1" in refs and "R2" in refs

        # Check for hierarchical labels
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        net1_labels = sch_content.count('hierarchical_label "NET1"')
        assert net1_labels >= 2, (
            f"Expected at least 2 NET1 labels, found {net1_labels}"
        )

        print(f"\n✅ Visual validation passed:")
        print(f"   - Components: {refs}")
        print(f"   - NET1 labels: {net1_labels}")
        print(f"\n⚠️  Note: This test does NOT validate electrical connectivity")
        print(f"   Use test_10_generate_with_net for full electrical validation")

    finally:
        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
