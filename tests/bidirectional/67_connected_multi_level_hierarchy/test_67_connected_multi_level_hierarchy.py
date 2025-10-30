#!/usr/bin/env python3
"""
Automated test for 67_connected_multi_level_hierarchy.

Tests incremental hierarchical development WITH electrical connections.

This validates that:
1. Start with single-level circuit (main with R1)
2. Add level1, pass Net("SIGNAL") → R1—R2 connected across sheets
3. Add level2, pass same net through → R1—R2—R3 all connected across 3 levels
4. Hierarchical pins and labels generated at each level
5. Netlist proves multi-level connectivity

This is the COMPLETE hierarchical workflow:
- Progressive subcircuit addition (like test 22)
- Cross-sheet connectivity via net passing (like test 24)
- Nested hierarchy with electrical connections through all levels

Workflow:
Step 1: main with R1 (1 level, no connections)
  - Verify: 1 sheet, R1 unconnected

Step 2: Add level1 with R1—R2 connected (2 levels)
  - Create Net("SIGNAL") in main
  - Connect R1[1] to signal
  - Pass signal to level1(signal_net=signal)
  - Connect R2[1] to signal_net in level1
  - Verify: 2 sheets, hierarchical pin/label "SIGNAL", R1—R2 connected

Step 3: Add level2 with R1—R2—R3 connected (3 levels)
  - Pass same signal from level1 to level2
  - Connect R3[1] to signal_net in level2
  - Verify: 3 sheets, hierarchical pins/labels at each level, R1—R2—R3 connected

Level 3 Validation:
- Netlist comparison to prove multi-level connectivity
- All three resistors on same net spanning 3 hierarchy levels
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
    node_pattern = r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)'
    net_blocks = re.split(r'\(net\s+\(code', netlist_content)

    for block in net_blocks:
        if '(name "' not in block:
            continue

        block = '(net (code' + block
        name_match = re.search(r'\(name\s+"([^"]+)"\)', block)
        if not name_match:
            continue

        net_name = name_match.group(1).strip('/')

        if net_name.startswith('unconnected-'):
            continue

        nodes = []
        for node_match in re.finditer(node_pattern, block):
            ref = node_match.group(1)
            pin = node_match.group(2)
            nodes.append((ref, pin))

        if nodes:
            nets[net_name] = sorted(nodes)

    return nets


def test_67_connected_multi_level_hierarchy(request):
    """Test connected multi-level hierarchy: R1—R2—R3 across 3 levels.

    COMPLETE HIERARCHICAL WORKFLOW:
    Combines progressive subcircuit addition with cross-sheet connectivity.

    This is the ultimate hierarchical test:
    - Add subcircuits incrementally (1→2→3 levels)
    - Pass Net through hierarchy (main → level1 → level2)
    - Components connected across all levels (R1—R2—R3)
    - Hierarchical infrastructure generated automatically

    If this works, hierarchical design is fully functional!

    Workflow:
    Step 1: main with R1 (unconnected)
    Step 2: Add level1, pass Net("SIGNAL") → R1—R2 connected
    Step 3: Add level2, pass same net → R1—R2—R3 all connected

    Level 3 Validation:
    - Netlist proves all resistors on same net
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "connected_hierarchy.py"
    output_dir = test_dir / "connected_hierarchy"
    main_schematic = output_dir / "connected_hierarchy.kicad_sch"
    level1_schematic = output_dir / "level1.kicad_sch"
    level2_schematic = output_dir / "level2.kicad_sch"

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
        # STEP 1: Generate single-level circuit (main with R1, unconnected)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate main with R1 (unconnected)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "connected_hierarchy.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 1 failed\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert main_schematic.exists(), "Main schematic not created"

        from kicad_sch_api import Schematic
        main_sch = Schematic.load(str(main_schematic))
        r1_step1 = main_sch.components[0]
        r1_step1_pos = r1_step1.position

        print(f"✅ Step 1: Single-level circuit")
        print(f"   - R1 position: {r1_step1_pos}")

        # =====================================================================
        # STEP 2: Add level1 with Net("SIGNAL") connecting R1—R2
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Add level1 with R1—R2 connected via Net(\"SIGNAL\")")
        print("="*70)

        # This step will XFAIL due to:
        # 1. Issue #406 - subcircuit generation broken
        # 2. Net passing syntax may need confirmation

        print(f"\n⚠️  Step 2 will XFAIL:")
        print(f"   - Issue #406: Subcircuit generation broken")
        print(f"   - Net passing syntax may need confirmation")

        pytest.xfail(
            "Connected multi-level hierarchy blocked by:\n"
            "  1. Issue #406 - subcircuit sheet generation broken\n"
            "  2. Test 22 - progressive subcircuit addition must pass first\n"
            "  3. Test 24 - cross-sheet connection must pass first\n"
            "\n"
            "This test documents the expected workflow for the complete\n"
            "hierarchical feature. It combines:\n"
            "  - Progressive hierarchy (test 22)\n"
            "  - Cross-sheet connectivity (test 24)\n"
            "  - Multi-level net passing\n"
            "\n"
            "Once dependencies are fixed, this test validates the ultimate\n"
            "hierarchical workflow: R1—R2—R3 connected across 3 levels."
        )

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
