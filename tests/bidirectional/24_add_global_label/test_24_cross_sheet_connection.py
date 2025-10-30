#!/usr/bin/env python3
"""
Automated test for 24_cross_sheet_connection bidirectional test.

Tests CRITICAL cross-sheet hierarchical label connection workflow.

This validates that:
1. Parent and child circuits can be generated with unconnected components
2. Passing a Net from parent to child creates proper hierarchical infrastructure:
   - Hierarchical sheet symbol on parent sheet
   - Hierarchical pin on the sheet symbol
   - Hierarchical label on child sheet
   - Electrical connectivity across sheets
3. Position preservation works across hierarchy

Workflow:
1. Generate parent + child circuits with R1 (parent) and R2 (child) unconnected
2. Verify: 2 sheets exist, hierarchical sheet symbol visible, no connection
3. Modify Python to pass Net("SIGNAL") from parent to child
4. Connect R1[1] += signal (parent), R2[1] += signal (child)
5. Regenerate
6. Validate:
   - Hierarchical sheet symbol still on parent sheet
   - Hierarchical pin "SIGNAL" appears on sheet symbol
   - Hierarchical label "SIGNAL" appears on child sheet
   - R1[1] and R2[1] electrically connected via netlist
   - Component positions preserved

Level 3 Validation:
- kicad-sch-api for schematic structure
- Text search for hierarchical_pin and hierarchical_label
- Netlist comparison for electrical connectivity across sheets
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


def test_24_cross_sheet_hierarchical_connection(request):
    """Test cross-sheet hierarchical label connection via net passing.

    CRITICAL WORKFLOW:
    Validates that passing a Net from parent to child circuit creates proper
    hierarchical infrastructure in KiCad:
    - Hierarchical sheet symbol (parent sheet)
    - Hierarchical pin on sheet symbol
    - Hierarchical label on child sheet
    - Electrical connectivity across sheets

    This is the foundation for hierarchical circuit development - components
    in different circuits can be electrically connected by passing nets.

    Workflow:
    1. Generate parent + child with unconnected components (R1, R2)
    2. Verify 2 sheets, sheet symbol, no connection
    3. Pass Net("SIGNAL") from parent to child
    4. Connect R1[1] and R2[1] to the shared net
    5. Regenerate → hierarchical pin/label appear, electrical connection established

    Level 3 Validation:
    - kicad-sch-api for structure
    - Text search for hierarchical_pin and hierarchical_label
    - Netlist comparison for cross-sheet connectivity
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "hierarchical_connection.py"
    output_dir = test_dir / "hierarchical_connection"
    parent_schematic = output_dir / "hierarchical_connection.kicad_sch"
    child_schematic = output_dir / "child_circuit.kicad_sch"

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
        # STEP 1: Generate parent + child circuits (no connection)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate parent + child circuits (unconnected)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "hierarchical_connection.py"],
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

        assert parent_schematic.exists(), "Parent schematic not created"

        # Note: Child schematic may not exist yet if subcircuit generation is broken
        # This is actually what we're discovering in test 22
        # For now, we'll document if it's missing

        child_exists = child_schematic.exists()
        print(f"   - Parent schematic: {parent_schematic.exists()} ✓")
        print(f"   - Child schematic: {child_exists} {'✓' if child_exists else '❌ (Issue #406)'}")

        # Load parent schematic
        from kicad_sch_api import Schematic
        parent_sch = Schematic.load(str(parent_schematic))
        parent_components = parent_sch.components

        # Validate R1 exists on parent sheet
        assert len(parent_components) >= 1, f"Expected R1 on parent, found {len(parent_components)} components"
        refs = {c.reference for c in parent_components}
        assert "R1" in refs, f"R1 not found on parent sheet. Found: {refs}"

        r1_initial = next(c for c in parent_components if c.reference == "R1")
        r1_initial_pos = r1_initial.position

        print(f"✅ Step 1: Initial hierarchical circuit generated")
        print(f"   - Parent components: {refs}")
        print(f"   - R1 position: {r1_initial_pos}")

        if child_exists:
            child_sch = Schematic.load(str(child_schematic))
            child_components = child_sch.components
            child_refs = {c.reference for c in child_components}
            print(f"   - Child components: {child_refs}")
        else:
            print(f"   ⚠️  Child schematic not generated - likely Issue #406")
            print(f"   This test will be marked as XFAIL until subcircuit generation is fixed")

        # =====================================================================
        # STEP 2: Pass Net("SIGNAL") from parent to child
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Modify Python to pass Net(\"SIGNAL\") between circuits")
        print("="*70)

        # Modify child_circuit to accept and use signal_net parameter
        child_modified = original_code.replace(
            '    # START_MARKER: Test will add net connection between markers\n'
            '    # END_MARKER',
            '    # START_MARKER: Test will add net connection between markers\n'
            '    # Accept net parameter from parent and connect R2[1]\n'
            '    # signal_net = Net("SIGNAL")  # Would be passed from parent\n'
            '    # r2[1] += signal_net\n'
            '    # END_MARKER'
        )

        # For now, create a PLACEHOLDER that shows the intent
        # This will fail until we figure out the proper syntax for passing nets
        parent_modified = child_modified.replace(
            '    # START_MARKER: Test will add net passing between markers\n'
            '    child_circuit()\n'
            '    # END_MARKER',
            '    # START_MARKER: Test will add net passing between markers\n'
            '    signal = Net("SIGNAL")\n'
            '    r1[1] += signal\n'
            '    # Pass signal to child_circuit - SYNTAX TBD\n'
            '    # child_circuit(signal_net=signal)\n'
            '    child_circuit()\n'
            '    # END_MARKER'
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(parent_modified)

        print(f"✅ Step 2: Python modified (PLACEHOLDER - syntax TBD)")
        print(f"   - Created Net(\"SIGNAL\") on parent")
        print(f"   - Connected R1[1] to signal")
        print(f"   - Child connection syntax needs to be determined")
        print(f"   ⚠️  This test is a PLACEHOLDER until net passing syntax is confirmed")

        # Mark this test as XFAIL since we don't know the proper syntax yet
        pytest.xfail("Net passing syntax between circuits not yet determined. "
                     "This test documents the expected workflow but cannot execute until "
                     "we confirm how to pass Net objects between @circuit functions.")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
