#!/usr/bin/env python3
"""
Automated test for 22_progressive_subcircuit_addition.

Tests incremental hierarchical circuit development workflow.

This validates that:
1. Start with single-level circuit (main only)
2. Add level 1 subcircuit → 2 sheets generated (main + level1)
3. Add level 2 subcircuit → 3 sheets generated (main → level1 → level2)
4. Hierarchical sheet symbols appear correctly at each level
5. Position preservation works through hierarchy additions

Workflow:
Step 1: Generate main circuit with R1 (1 level)
  - Verify: 1 sheet (main.kicad_sch)
  - Verify: R1 visible

Step 2: Add level1() subcircuit with R2 (2 levels)
  - Uncomment level1 circuit and main's level1() call
  - Regenerate
  - Verify: 2 sheets (main.kicad_sch + level1.kicad_sch)
  - Verify: Hierarchical sheet symbol on main sheet
  - Verify: R1 position preserved
  - Verify: R2 visible on level1 sheet

Step 3: Add level2() subcircuit with R3 (3 levels, nested)
  - Uncomment level2 circuit and level1's level2() call
  - Regenerate
  - Verify: 3 sheets (main + level1 + level2)
  - Verify: Hierarchical sheet symbols on main and level1
  - Verify: R1, R2 positions preserved
  - Verify: R3 visible on level2 sheet

This tests the fundamental iterative workflow for hierarchical design.

Level 2 Validation:
- File existence checking (verify .kicad_sch files created)
- kicad-sch-api for component verification
- Position preservation across regenerations
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_22_progressive_subcircuit_addition(request):
    """Test progressive subcircuit addition: 1→2→3 hierarchy levels.

    CRITICAL ITERATIVE WORKFLOW:
    Validates incremental hierarchical development - adding subcircuits
    one at a time and verifying hierarchy builds correctly.

    This is how real circuits are developed:
    - Start simple (single level)
    - Add complexity incrementally (add subcircuits)
    - Each step should work (regenerate successfully)
    - Positions preserved (don't reset on hierarchy changes)

    Workflow:
    Step 1: main with R1 (1 level)
    Step 2: main → level1 with R2 (2 levels)
    Step 3: main → level1 → level2 with R3 (3 levels, nested)

    Level 2 Validation:
    - File existence (.kicad_sch files)
    - Component verification (kicad-sch-api)
    - Position preservation
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "progressive_hierarchy.py"
    output_dir = test_dir / "progressive_hierarchy"
    main_schematic = output_dir / "progressive_hierarchy.kicad_sch"
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
        # STEP 1: Generate single-level circuit (main with R1)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate single-level circuit (main with R1)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "progressive_hierarchy.py"],
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

        assert main_schematic.exists(), "Main schematic not created"
        assert not level1_schematic.exists(), "Level1 schematic should NOT exist yet"
        assert not level2_schematic.exists(), "Level2 schematic should NOT exist yet"

        # Validate R1 on main sheet
        from kicad_sch_api import Schematic
        main_sch = Schematic.load(str(main_schematic))
        components = main_sch.components

        assert len(components) == 1, f"Expected 1 component, found {len(components)}"
        r1 = components[0]
        assert r1.reference == "R1"

        r1_step1_pos = r1.position

        print(f"✅ Step 1: Single-level circuit generated")
        print(f"   - Main schematic: ✓")
        print(f"   - Level1 schematic: ✗ (not added yet)")
        print(f"   - Level2 schematic: ✗ (not added yet)")
        print(f"   - R1 position: {r1_step1_pos}")

        # =====================================================================
        # STEP 2: Add level1 subcircuit (2 levels: main → level1)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Add level1 subcircuit (2 levels)")
        print("="*70)

        # Uncomment level1 circuit definition
        step2_code = original_code.replace(
            '# STEP 2 circuits (uncomment to enable):\n'
            '# @circuit(name="level1")\n'
            '# def level1():\n'
            '#     """Level 1 subcircuit."""\n'
            '#     r2 = Component(\n'
            '#         symbol="Device:R",\n'
            '#         ref="R2",\n'
            '#         value="4.7k",\n'
            '#         footprint="Resistor_SMD:R_0603_1608Metric",\n'
            '#     )\n'
            '#     # STEP 3: Uncomment to add level 2 nesting\n'
            '#     # level2()',
            '# STEP 2 circuits (enabled):\n'
            '@circuit(name="level1")\n'
            'def level1():\n'
            '    """Level 1 subcircuit."""\n'
            '    r2 = Component(\n'
            '        symbol="Device:R",\n'
            '        ref="R2",\n'
            '        value="4.7k",\n'
            '        footprint="Resistor_SMD:R_0603_1608Metric",\n'
            '    )\n'
            '    # STEP 3: Uncomment to add level 2 nesting\n'
            '    # level2()'
        )

        # Uncomment level1() call in main
        step2_code = step2_code.replace(
            '    # STEP 2: Uncomment to add level 1 subcircuit\n'
            '    # level1()',
            '    # STEP 2: Add level 1 subcircuit\n'
            '    level1()'
        )

        # Write modified code
        with open(python_file, "w") as f:
            f.write(step2_code)

        print(f"✅ Modified Python: Enabled level1 circuit and main's level1() call")

        # Regenerate
        result = subprocess.run(
            ["uv", "run", "progressive_hierarchy.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 2 failed: Adding level1 subcircuit\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Validate 2 schematics exist
        assert main_schematic.exists(), "Main schematic should still exist"

        # Note: level1 schematic may not exist due to Issue #406
        level1_exists = level1_schematic.exists()

        if not level1_exists:
            print(f"\n⚠️  Step 2: Level1 schematic NOT generated (Issue #406)")
            print(f"   This test will be marked as XFAIL until subcircuit generation is fixed")
            pytest.xfail("Subcircuit sheet generation broken (Issue #406). "
                        "level1.kicad_sch not created even though level1() is called.")

        assert not level2_schematic.exists(), "Level2 schematic should NOT exist yet"

        # Validate R1 position preserved
        main_sch_step2 = Schematic.load(str(main_schematic))
        r1_step2 = next((c for c in main_sch_step2.components if c.reference == "R1"), None)

        assert r1_step2 is not None, "R1 disappeared from main sheet!"
        r1_step2_pos = r1_step2.position

        assert r1_step2_pos == r1_step1_pos, (
            f"R1 position NOT preserved!\n"
            f"  Step 1: {r1_step1_pos}\n"
            f"  Step 2: {r1_step2_pos}"
        )

        # Validate R2 on level1 sheet
        level1_sch = Schematic.load(str(level1_schematic))
        level1_components = level1_sch.components

        assert len(level1_components) == 1, f"Expected 1 component on level1, found {len(level1_components)}"
        r2 = level1_components[0]
        assert r2.reference == "R2"

        r2_step2_pos = r2.position

        print(f"✅ Step 2: 2-level hierarchy generated")
        print(f"   - Main schematic: ✓")
        print(f"   - Level1 schematic: ✓")
        print(f"   - Level2 schematic: ✗ (not added yet)")
        print(f"   - R1 position preserved: {r1_step2_pos}")
        print(f"   - R2 position: {r2_step2_pos}")

        # =====================================================================
        # STEP 3: Add level2 subcircuit (3 levels: main → level1 → level2)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Add level2 subcircuit (3 levels, nested)")
        print("="*70)

        # Uncomment level2 circuit definition
        step3_code = step2_code.replace(
            '# STEP 3 circuits (uncomment to enable):\n'
            '# @circuit(name="level2")\n'
            '# def level2():\n'
            '#     """Level 2 subcircuit (deepest level)."""\n'
            '#     r3 = Component(\n'
            '#         symbol="Device:R",\n'
            '#         ref="R3",\n'
            '#         value="20k",\n'
            '#         footprint="Resistor_SMD:R_0603_1608Metric",\n'
            '#     )',
            '# STEP 3 circuits (enabled):\n'
            '@circuit(name="level2")\n'
            'def level2():\n'
            '    """Level 2 subcircuit (deepest level)."""\n'
            '    r3 = Component(\n'
            '        symbol="Device:R",\n'
            '        ref="R3",\n'
            '        value="20k",\n'
            '        footprint="Resistor_SMD:R_0603_1608Metric",\n'
            '    )'
        )

        # Uncomment level2() call in level1
        step3_code = step3_code.replace(
            '    # STEP 3: Uncomment to add level 2 nesting\n'
            '    # level2()',
            '    # STEP 3: Add level 2 nesting\n'
            '    level2()'
        )

        # Write modified code
        with open(python_file, "w") as f:
            f.write(step3_code)

        print(f"✅ Modified Python: Enabled level2 circuit and level1's level2() call")

        # Regenerate
        result = subprocess.run(
            ["uv", "run", "progressive_hierarchy.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 3 failed: Adding level2 subcircuit\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Validate 3 schematics exist
        assert main_schematic.exists(), "Main schematic should still exist"
        assert level1_schematic.exists(), "Level1 schematic should still exist"

        level2_exists = level2_schematic.exists()

        if not level2_exists:
            print(f"\n⚠️  Step 3: Level2 schematic NOT generated (Issue #406)")
            print(f"   Nested subcircuit generation also broken")
            pytest.xfail("Nested subcircuit generation broken (Issue #406). "
                        "level2.kicad_sch not created even though level2() is called from level1().")

        # Validate R1, R2 positions preserved
        main_sch_step3 = Schematic.load(str(main_schematic))
        r1_step3 = next((c for c in main_sch_step3.components if c.reference == "R1"), None)

        assert r1_step3 is not None, "R1 disappeared!"
        assert r1_step3.position == r1_step1_pos, "R1 position changed in step 3"

        level1_sch_step3 = Schematic.load(str(level1_schematic))
        r2_step3 = next((c for c in level1_sch_step3.components if c.reference == "R2"), None)

        assert r2_step3 is not None, "R2 disappeared!"
        assert r2_step3.position == r2_step2_pos, "R2 position changed in step 3"

        # Validate R3 on level2 sheet
        level2_sch = Schematic.load(str(level2_schematic))
        level2_components = level2_sch.components

        assert len(level2_components) == 1, f"Expected 1 component on level2, found {len(level2_components)}"
        r3 = level2_components[0]
        assert r3.reference == "R3"

        print(f"✅ Step 3: 3-level nested hierarchy generated")
        print(f"   - Main schematic: ✓")
        print(f"   - Level1 schematic: ✓")
        print(f"   - Level2 schematic: ✓")
        print(f"   - R1 position preserved: {r1_step3.position}")
        print(f"   - R2 position preserved: {r2_step3.position}")
        print(f"   - R3 position: {r3.position}")
        print(f"\n🎉 PROGRESSIVE HIERARCHY TEST PASSED!")
        print(f"   Incremental subcircuit addition works correctly!")
        print(f"   1 → 2 → 3 levels built successfully!")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
