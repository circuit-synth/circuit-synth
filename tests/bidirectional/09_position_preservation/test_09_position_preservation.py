#!/usr/bin/env python3
"""
Automated test for 09_position_preservation bidirectional test.

Tests THE KILLER FEATURE: Position preservation when adding components during
iterative development.

Core Question: When you add R2 to Python and regenerate, does R1 stay at its
manually-positioned location, or does it get moved back to default?

This is critical because if positions aren't preserved, users lose all their
layout work every time they regenerate - making the tool unusable for real work.

Workflow:
1. Generate KiCad with R1 → R1 at default auto-placed position
2. Manually move R1 in KiCad to specific position (e.g., 100, 50)
3. Add R2 to Python code
4. Regenerate KiCad from Python
5. Validate:
   - R1 stays at manually-moved position (NOT reset to default!)
   - R2 auto-placed at new position
   - Manual layout work preserved

Validation uses kicad-sch-api.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_09_position_preservation(request):
    """Test position preservation when adding components during iterative development.

    THE KILLER FEATURE TEST:
    Validates that manually-positioned components (R1) stay in place when
    adding new components (R2) and regenerating from Python.

    Workflow:
    1. Generate with R1 → auto-placed at default position
    2. Manually move R1 to (100, 50) via direct file edit
    3. Add R2 to Python code
    4. Regenerate → R1 should stay at (100, 50), R2 auto-placed

    Why critical:
    - Without this, layout work is lost every regeneration
    - Tool becomes unusable for iterative development
    - This is THE feature that makes bidirectional sync valuable

    Level 2 Semantic Validation:
    - kicad-sch-api for position validation
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "single_resistor.py"
    output_dir = test_dir / "single_resistor"
    schematic_file = output_dir / "single_resistor.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file (R1 only)
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate KiCad with R1 only
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with R1 (auto-placed position)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "single_resistor.py"],
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

        # Get R1's auto-placed default position
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 1
        r1_initial = components[0]
        assert r1_initial.reference == "R1"

        default_pos = r1_initial.position
        print(f"✅ Step 1: R1 generated at default position")
        print(f"   - Reference: {r1_initial.reference}")
        print(f"   - Default position: {default_pos}")

        # =====================================================================
        # STEP 2: Manually move R1 to specific position (100, 50)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Manually move R1 to (100, 50)")
        print("="*70)

        # Read schematic file
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        # Find R1 symbol block
        r1_ref_pos = sch_content.find('(property "Reference" "R1"')
        assert r1_ref_pos != -1, "Could not find R1 in schematic"

        # Find symbol block start
        symbol_start = sch_content.rfind('(symbol', 0, r1_ref_pos)
        assert symbol_start != -1

        # Find matching closing parenthesis
        paren_count = 0
        i = symbol_start
        symbol_end = -1

        while i < len(sch_content):
            if sch_content[i] == '(':
                paren_count += 1
            elif sch_content[i] == ')':
                paren_count -= 1
                if paren_count == 0:
                    symbol_end = i + 1
                    break
            i += 1

        assert symbol_end != -1, "Could not find closing parenthesis for R1"

        # Extract and modify R1 block to move to (100, 50)
        r1_block = sch_content[symbol_start:symbol_end]

        # Modify position: (symbol ... (at X Y ANGLE) ...)
        r1_block_moved = re.sub(
            r'\(at\s+[\d.]+\s+[\d.]+\s+[\d.]+\)',
            '(at 100 50 0)',
            r1_block,
            count=1
        )

        # Replace in schematic
        sch_content_moved = (
            sch_content[:symbol_start] +
            r1_block_moved +
            sch_content[symbol_end:]
        )

        # Write modified schematic
        with open(schematic_file, 'w') as f:
            f.write(sch_content_moved)

        # Verify R1 moved to (100, 50)
        sch_moved = Schematic.load(str(schematic_file))
        r1_moved = sch_moved.components[0]
        moved_pos = r1_moved.position

        assert moved_pos.x == 100.0 and moved_pos.y == 50.0, (
            f"R1 should be at (100, 50), got {moved_pos}"
        )

        print(f"✅ Step 2: R1 manually moved to (100, 50)")
        print(f"   - Previous position: {default_pos}")
        print(f"   - New position: {moved_pos}")

        # =====================================================================
        # STEP 3: Add R2 to Python code
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Add R2 to Python code")
        print("="*70)

        # Add R2 after R1 in Python code
        # Find the closing parenthesis of r1 Component definition
        r1_end_pattern = r'(r1 = Component\([^)]+\))'

        r2_code = '''

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )'''

        modified_code = re.sub(
            r1_end_pattern,
            r'\1' + r2_code,
            original_code,
            count=1
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 3: R2 added to Python code")

        # =====================================================================
        # STEP 4: Regenerate KiCad from modified Python
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Regenerate KiCad with R1 + R2")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "single_resistor.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration with R2\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # =====================================================================
        # STEP 5: Validate R1 position preserved, R2 auto-placed
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate position preservation (THE KILLER FEATURE)")
        print("="*70)

        sch_final = Schematic.load(str(schematic_file))
        components_final = sch_final.components

        assert len(components_final) == 2, (
            f"Expected 2 components (R1, R2), found {len(components_final)}"
        )

        # Find R1 and R2
        r1_final = next((c for c in components_final if c.reference == "R1"), None)
        r2_final = next((c for c in components_final if c.reference == "R2"), None)

        assert r1_final is not None, "R1 not found in regenerated schematic"
        assert r2_final is not None, "R2 not found in regenerated schematic"

        r1_final_pos = r1_final.position
        r2_final_pos = r2_final.position

        # CRITICAL VALIDATION: R1 position preserved at (100, 50)
        assert r1_final_pos.x == 100.0 and r1_final_pos.y == 50.0, (
            f"❌ POSITION NOT PRESERVED! R1 should stay at (100, 50)\n"
            f"   But R1 moved back to {r1_final_pos}\n"
            f"   This means manual layout work is lost every regeneration!\n"
            f"   THE KILLER FEATURE IS BROKEN!"
        )

        # R2 should be auto-placed at different position
        assert r2_final_pos != r1_final_pos, (
            f"R2 should be auto-placed at different position than R1"
        )

        print(f"✅ Step 5: Position preservation VERIFIED!")
        print(f"   - R1 preserved at: {r1_final_pos} ✓")
        print(f"   - R2 auto-placed at: {r2_final_pos} ✓")
        print(f"   - Manual layout work NOT lost ✓")
        print(f"\n🎉 THE KILLER FEATURE WORKS!")
        print(f"   Iterative development workflow is viable!")
        print(f"   Users can add components without losing layout work!")

    finally:
        # Restore original Python file (R1 only)
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
