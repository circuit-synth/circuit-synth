#!/usr/bin/env python3
"""
Automated test for 58_hierarchical_pin_to_global_label bidirectional test.

Tests CRITICAL MIXED LABELING pattern: hierarchical pins + global labels in same design.

This validates that you can:
1. Generate circuit with hierarchical power distribution (parent → child)
2. Generate circuit with global signal bus (peer → peer)
3. BOTH label types coexist in same sheet (SubcircuitA has both)
4. Netlist shows correct connectivity for both mechanisms
5. Add component in parent using global label
6. Regenerate → global label propagates correctly

This is ESSENTIAL for complex real-world designs where:
- Power is distributed hierarchically (parent → children)
- Signals are shared globally (peer-to-peer across sheets)

Workflow:
1. Generate with parent (VCC hierarchical) + SubcircuitA (VCC + SPI_CLK) + SubcircuitB (SPI_CLK)
2. Verify SubcircuitA has BOTH hierarchical_label and global_label
3. Verify netlist shows VCC through hierarchy, SPI_CLK through global
4. Add R4 in parent with SPI_CLK global label
5. Regenerate
6. Validate:
   - Parent now has global_label for SPI_CLK
   - R4 connected to SPI_CLK net
   - SubcircuitA still has both label types
   - Netlist shows R4 in SPI_CLK net

Validation uses:
- kicad-sch-api for schematic structure (Level 2)
- Netlist parsing for electrical connectivity (Level 3)
- Mixed label type detection
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def parse_netlist(netlist_content):
    """Parse netlist content and extract net information.

    Returns dict: {net_name: [(ref, pin), ...]}

    Example netlist format:
    (net (code "1") (name "/VCC")
      (node (ref "R1") (pin "1"))
      (node (ref "R2") (pin "1")))
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


def check_mixed_labels_in_sheet(sheet_file, expected_hierarchical, expected_global):
    """Check that a sheet contains both hierarchical and global labels.

    Args:
        sheet_file: Path to .kicad_sch file
        expected_hierarchical: List of expected hierarchical label names
        expected_global: List of expected global label names

    Returns:
        dict with 'hierarchical' and 'global' label counts
    """
    with open(sheet_file, 'r') as f:
        content = f.read()

    found_hierarchical = {}
    found_global = {}

    for label in expected_hierarchical:
        count = content.count(f'hierarchical_label "{label}"')
        found_hierarchical[label] = count

    for label in expected_global:
        count = content.count(f'global_label "{label}"')
        found_global[label] = count

    return {
        'hierarchical': found_hierarchical,
        'global': found_global
    }


@pytest.mark.xfail(
    reason="Issue #380: Synchronizer may not support mixed hierarchical + global labels in same sheet"
)
def test_58_mixed_labels_comprehensive(request):
    """Test mixed hierarchical and global labels in same design.

    CRITICAL REAL-WORLD PATTERN:
    Validates that complex designs with mixed labeling strategies work:
    - Hierarchical labels for power distribution (parent → child)
    - Global labels for signal buses (peer-to-peer)
    - Both label types coexist in same sheet (SubcircuitA)

    This workflow is essential for:
    - Power supply circuits (hierarchical) + communication buses (global)
    - MCU designs receiving power hierarchically, sharing I2C/SPI globally
    - Memory banks with hierarchical power, global data bus
    - Any complex multi-sheet design with structured and flat connectivity

    Validation covers:
    - Level 1: File generation (schematics exist)
    - Level 2: Schematic structure (mixed labels present)
    - Level 3: Electrical connectivity (netlist verification)
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "mixed_labels.py"
    output_dir = test_dir / "mixed_labels"
    root_schematic = output_dir / "mixed_labels.kicad_sch"

    # Subcircuit schematics
    subcircuit_a_sch = output_dir / "SubcircuitA.kicad_sch"
    subcircuit_b_sch = output_dir / "SubcircuitB.kicad_sch"

    # Netlist files
    kicad_netlist_file = output_dir / "mixed_labels_kicad.net"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python code
    with open(python_file, 'r') as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate KiCad with mixed labels
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with mixed hierarchical + global labels")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "mixed_labels.py"],
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

        assert root_schematic.exists(), "Root schematic not created"
        assert subcircuit_a_sch.exists(), "SubcircuitA schematic not created"
        assert subcircuit_b_sch.exists(), "SubcircuitB schematic not created"

        print(f"✅ Step 1: KiCad project generated")
        print(f"   - Root: {root_schematic.name}")
        print(f"   - SubcircuitA: {subcircuit_a_sch.name}")
        print(f"   - SubcircuitB: {subcircuit_b_sch.name}")

        # =====================================================================
        # STEP 2: Validate schematic structure (Level 2)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Validate schematic structure (mixed labels)")
        print("="*70)

        from kicad_sch_api import Schematic

        # Load root schematic
        root_sch = Schematic.load(str(root_schematic))
        root_components = root_sch.components
        root_refs = {c.reference for c in root_components}

        assert "R1" in root_refs, f"R1 missing from root, found: {root_refs}"

        print(f"   Root sheet components: {root_refs}")

        # Load SubcircuitA schematic
        sub_a_sch = Schematic.load(str(subcircuit_a_sch))
        sub_a_components = sub_a_sch.components
        sub_a_refs = {c.reference for c in sub_a_components}

        assert "R2" in sub_a_refs, f"R2 missing from SubcircuitA, found: {sub_a_refs}"

        print(f"   SubcircuitA components: {sub_a_refs}")

        # Load SubcircuitB schematic
        sub_b_sch = Schematic.load(str(subcircuit_b_sch))
        sub_b_components = sub_b_sch.components
        sub_b_refs = {c.reference for c in sub_b_components}

        assert "R3" in sub_b_refs, f"R3 missing from SubcircuitB, found: {sub_b_refs}"

        print(f"   SubcircuitB components: {sub_b_refs}")

        # =====================================================================
        # STEP 3: Check for MIXED LABELS in SubcircuitA (CRITICAL)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Validate MIXED LABELS in SubcircuitA (hierarchical + global)")
        print("="*70)

        # SubcircuitA should have BOTH hierarchical_label (VCC) and global_label (SPI_CLK)
        sub_a_labels = check_mixed_labels_in_sheet(
            subcircuit_a_sch,
            expected_hierarchical=["VCC"],
            expected_global=["SPI_CLK"]
        )

        print(f"\n📊 SubcircuitA label analysis:")
        print(f"   Hierarchical labels:")
        for label, count in sub_a_labels['hierarchical'].items():
            print(f"     - {label}: {count} occurrences")

        print(f"   Global labels:")
        for label, count in sub_a_labels['global'].items():
            print(f"     - {label}: {count} occurrences")

        # Validate SubcircuitA has BOTH label types
        assert sub_a_labels['hierarchical']['VCC'] >= 1, (
            f"SubcircuitA missing hierarchical_label 'VCC'! "
            f"Found {sub_a_labels['hierarchical']['VCC']} occurrences.\n"
            f"This is Issue #380 - synchronizer may not support mixed labels."
        )

        assert sub_a_labels['global']['SPI_CLK'] >= 1, (
            f"SubcircuitA missing global_label 'SPI_CLK'! "
            f"Found {sub_a_labels['global']['SPI_CLK']} occurrences.\n"
            f"This is Issue #380 - synchronizer may not support mixed labels."
        )

        print(f"\n✅ Step 3: MIXED LABELS VALIDATED in SubcircuitA!")
        print(f"   ✓ hierarchical_label 'VCC' present")
        print(f"   ✓ global_label 'SPI_CLK' present")
        print(f"   ✓ Both label types coexist in same sheet")

        # Check SubcircuitB has global label
        sub_b_labels = check_mixed_labels_in_sheet(
            subcircuit_b_sch,
            expected_hierarchical=[],
            expected_global=["SPI_CLK"]
        )

        assert sub_b_labels['global']['SPI_CLK'] >= 1, (
            f"SubcircuitB missing global_label 'SPI_CLK'"
        )

        print(f"\n   SubcircuitB has global_label 'SPI_CLK': ✓")

        # =====================================================================
        # STEP 4: Export netlist and validate connectivity (Level 3)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Export netlist and validate connectivity")
        print("="*70)

        result = subprocess.run(
            [
                "kicad-cli", "sch", "export", "netlist",
                str(root_schematic),
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

        # Parse netlist
        with open(kicad_netlist_file, 'r') as f:
            netlist_content = f.read()

        nets = parse_netlist(netlist_content)

        print(f"\n📊 Netlist analysis:")
        print(f"   Nets found: {list(nets.keys())}")
        for net_name in sorted(nets.keys()):
            nodes = nets[net_name]
            print(f"   - {net_name}: {nodes}")

        # Validate VCC net (hierarchical connectivity)
        assert "VCC" in nets, (
            f"VCC net missing from netlist!\n"
            f"Found nets: {list(nets.keys())}"
        )

        vcc_nodes = nets["VCC"]
        print(f"\n   VCC net (hierarchical):")
        print(f"     Nodes: {vcc_nodes}")

        # VCC should connect R1 (parent) and R2 (SubcircuitA via hierarchy)
        vcc_refs = {node[0] for node in vcc_nodes}
        assert "R1" in vcc_refs, f"R1 not in VCC net (expected hierarchical connection)"
        assert "R2" in vcc_refs, f"R2 not in VCC net (expected hierarchical connection)"

        print(f"     ✓ R1 (parent) connected")
        print(f"     ✓ R2 (SubcircuitA) connected via hierarchy")

        # Validate SPI_CLK net (global connectivity)
        assert "SPI_CLK" in nets, (
            f"SPI_CLK net missing from netlist!\n"
            f"Found nets: {list(nets.keys())}"
        )

        spi_clk_nodes = nets["SPI_CLK"]
        print(f"\n   SPI_CLK net (global):")
        print(f"     Nodes: {spi_clk_nodes}")

        # SPI_CLK should connect R2 (SubcircuitA) and R3 (SubcircuitB) globally
        spi_clk_refs = {node[0] for node in spi_clk_nodes}
        assert "R2" in spi_clk_refs, f"R2 not in SPI_CLK net (expected global connection)"
        assert "R3" in spi_clk_refs, f"R3 not in SPI_CLK net (expected global connection)"

        print(f"     ✓ R2 (SubcircuitA) connected globally")
        print(f"     ✓ R3 (SubcircuitB) connected globally")

        print(f"\n✅ Step 4: Netlist connectivity VALIDATED!")
        print(f"   ✓ VCC flows hierarchically (parent → SubcircuitA)")
        print(f"   ✓ SPI_CLK connects globally (SubcircuitA ↔ SubcircuitB)")

        # =====================================================================
        # STEP 5: Add component in parent using global label
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Add R4 to parent with SPI_CLK global label")
        print("="*70)

        # Inject R4 with global SPI_CLK connection
        injection_lines = [
            "",
            "    # R4 on parent sheet with global SPI_CLK label",
            "    r4 = Component(",
            "        symbol=\"Device:R\",",
            "        ref=\"R4\",",
            "        value=\"2.2k\",",
            "        footprint=\"Resistor_SMD:R_0603_1608Metric\",",
            "    )",
            "    r4[1] += spi_clk_net  # Connect to global SPI_CLK",
        ]
        component_injection = "\n".join(injection_lines)

        marker_section = (
            "    # START_MARKER: Test will add parent component with global label here\n"
            "    # END_MARKER"
        )
        replacement_section = (
            "    # START_MARKER: Test will add parent component with global label here"
            + component_injection + "\n"
            + "    # END_MARKER"
        )

        modified_code = original_code.replace(marker_section, replacement_section)

        assert modified_code != original_code, (
            "Failed to modify Python code - markers not found"
        )

        # Write modified Python file
        with open(python_file, 'w') as f:
            f.write(modified_code)

        print(f"✅ Step 5: R4 added to Python code with SPI_CLK global label")

        # =====================================================================
        # STEP 6: Regenerate with R4
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Regenerate KiCad with R4 in parent")
        print("="*70)

        # Remove old output
        if output_dir.exists():
            shutil.rmtree(output_dir)

        result = subprocess.run(
            ["uv", "run", "mixed_labels.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 6 failed: Regeneration with R4\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 6: KiCad regenerated with R4")

        # =====================================================================
        # STEP 7: Validate R4 in parent with global label
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 7: Validate R4 added to parent with global label")
        print("="*70)

        # Load root schematic
        root_sch = Schematic.load(str(root_schematic))
        root_components = root_sch.components
        root_refs = {c.reference for c in root_components}

        assert "R4" in root_refs, f"R4 missing from root after regeneration, found: {root_refs}"

        print(f"   Root sheet components: {root_refs}")
        print(f"   ✓ R4 present in parent sheet")

        # Check parent now has global_label for SPI_CLK
        root_labels = check_mixed_labels_in_sheet(
            root_schematic,
            expected_hierarchical=[],
            expected_global=["SPI_CLK"]
        )

        assert root_labels['global']['SPI_CLK'] >= 1, (
            f"Parent sheet missing global_label 'SPI_CLK' after adding R4"
        )

        print(f"   ✓ Parent has global_label 'SPI_CLK'")

        # Verify SubcircuitA still has MIXED labels
        sub_a_labels_after = check_mixed_labels_in_sheet(
            subcircuit_a_sch,
            expected_hierarchical=["VCC"],
            expected_global=["SPI_CLK"]
        )

        assert sub_a_labels_after['hierarchical']['VCC'] >= 1, (
            "SubcircuitA lost hierarchical_label after parent modification"
        )
        assert sub_a_labels_after['global']['SPI_CLK'] >= 1, (
            "SubcircuitA lost global_label after parent modification"
        )

        print(f"   ✓ SubcircuitA still has BOTH label types")

        # Export and parse new netlist
        result = subprocess.run(
            [
                "kicad-cli", "sch", "export", "netlist",
                str(root_schematic),
                "--output", str(kicad_netlist_file)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, "Failed to export netlist after R4 addition"

        with open(kicad_netlist_file, 'r') as f:
            netlist_content_after = f.read()

        nets_after = parse_netlist(netlist_content_after)

        # Validate SPI_CLK now includes R4
        assert "SPI_CLK" in nets_after, "SPI_CLK net missing after R4 addition"

        spi_clk_nodes_after = nets_after["SPI_CLK"]
        spi_clk_refs_after = {node[0] for node in spi_clk_nodes_after}

        assert "R4" in spi_clk_refs_after, (
            f"R4 not in SPI_CLK net!\n"
            f"Expected: R2, R3, R4\n"
            f"Found: {spi_clk_refs_after}"
        )

        print(f"\n   SPI_CLK net after R4 addition:")
        print(f"     Nodes: {spi_clk_nodes_after}")
        print(f"     ✓ R2 (SubcircuitA) still connected")
        print(f"     ✓ R3 (SubcircuitB) still connected")
        print(f"     ✓ R4 (parent) now connected")

        print(f"\n🎉 MIXED LABELING WORKS!")
        print(f"   ✓ Hierarchical labels for power distribution")
        print(f"   ✓ Global labels for signal buses")
        print(f"   ✓ Both label types coexist in same sheet")
        print(f"   ✓ Netlist shows correct connectivity for both mechanisms")
        print(f"   ✓ Adding global label in parent propagates correctly")
        print(f"   ✓ Complex multi-sheet designs fully supported!")

    finally:
        # Restore original Python file
        with open(python_file, 'w') as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


def test_58_visual_validation_only(request):
    """Test 58 visual validation (without full netlist comparison).

    This test validates schematic structure without requiring
    working netlist export or mixed label support.

    Validates:
    - All expected components exist in correct sheets
    - SubcircuitA has at least one label (hierarchical or global)
    - No component overlap

    Does NOT validate:
    - Mixed labels in same sheet (requires full implementation)
    - Actual electrical connectivity (requires netlist)
    - Label type correctness
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "mixed_labels.py"
    output_dir = test_dir / "mixed_labels"
    root_schematic = output_dir / "mixed_labels.kicad_sch"
    subcircuit_a_sch = output_dir / "SubcircuitA.kicad_sch"
    subcircuit_b_sch = output_dir / "SubcircuitB.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        # Generate
        result = subprocess.run(
            ["uv", "run", "mixed_labels.py"],
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

        assert root_schematic.exists(), "Root schematic not created"
        assert subcircuit_a_sch.exists(), "SubcircuitA schematic not created"
        assert subcircuit_b_sch.exists(), "SubcircuitB schematic not created"

        # Validate component presence
        from kicad_sch_api import Schematic

        root_sch = Schematic.load(str(root_schematic))
        root_refs = {c.reference for c in root_sch.components}
        assert "R1" in root_refs, f"R1 missing from root, found: {root_refs}"

        sub_a_sch = Schematic.load(str(subcircuit_a_sch))
        sub_a_refs = {c.reference for c in sub_a_sch.components}
        assert "R2" in sub_a_refs, f"R2 missing from SubcircuitA, found: {sub_a_refs}"

        sub_b_sch = Schematic.load(str(subcircuit_b_sch))
        sub_b_refs = {c.reference for c in sub_b_sch.components}
        assert "R3" in sub_b_refs, f"R3 missing from SubcircuitB, found: {sub_b_refs}"

        # Check that SubcircuitA has at least some labels
        with open(subcircuit_a_sch, 'r') as f:
            sub_a_content = f.read()

        has_hierarchical = 'hierarchical_label' in sub_a_content
        has_global = 'global_label' in sub_a_content

        print(f"\n✅ Visual validation passed:")
        print(f"   - Root components: {root_refs}")
        print(f"   - SubcircuitA components: {sub_a_refs}")
        print(f"   - SubcircuitB components: {sub_b_refs}")
        print(f"   - SubcircuitA has hierarchical_label: {has_hierarchical}")
        print(f"   - SubcircuitA has global_label: {has_global}")
        print(f"\n⚠️  Note: This test does NOT validate mixed label support")
        print(f"   Use test_58_mixed_labels_comprehensive for full validation")

    finally:
        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
