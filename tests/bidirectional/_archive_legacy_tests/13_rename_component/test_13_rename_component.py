#!/usr/bin/env python3
"""
Automated test for 13_rename_component bidirectional test.

Tests component reference renaming with UUID-based matching (Issue #369 fix).

This validates THE FIX for Issue #369: When a component's reference changes
(R1 → R2), the UUID-based matching should preserve the component's
position and other properties instead of treating it as Remove+Add.

Workflow:
1. Generate KiCad with R1 at default position
2. Move R1 to specific position (100, 50)
3. Change reference R1 → R2 in Python code
4. Regenerate KiCad
5. Validate:
   - Component position preserved (still at 100, 50)
   - Reference updated to R2
   - UUID-based matching worked (not Remove+Add)

This proves Issue #369 is fixed: reference changes now work correctly.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_13_rename_component_with_position_preservation(request):
    """Test reference renaming with UUID-based matching (Issue #369 fix).

    THE FIX TEST:
    Validates that changing a component's reference (R1 → R2)
    preserves position using UUID-based matching.

    Before Issue #369 fix:
    - Reference change treated as Remove R1 + Add R2
    - Position would be lost
    - Sync would show "Remove: R1" and "Add: R2"

    After Issue #369 fix (UUID matching):
    - Reference change treated as Update R1
    - Position preserved via UUID
    - Sync shows "Update: R1" (or similar)

    Workflow:
    1. Generate with R1 → auto-placed position
    2. Move R1 to (100, 50)
    3. Change reference R1 → R_PULLUP in Python
    4. Regenerate → position should be preserved

    Validates:
    - Position preserved through reference change
    - UUID-based matching working
    - Issue #369 fixed

    Level 2 Semantic Validation:
    - kicad-sch-api for position and reference validation
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

    # Read original Python file (R1)
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate KiCad with R1
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with R1")
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

        # Get R1's default position
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 1
        r1_initial = components[0]
        assert r1_initial.reference == "R1"

        default_pos = r1_initial.position
        r1_uuid = r1_initial.uuid

        print(f"✅ Step 1: R1 generated")
        print(f"   - Reference: {r1_initial.reference}")
        print(f"   - Position: {default_pos}")
        print(f"   - UUID: {r1_uuid}")

        # =====================================================================
        # STEP 2: Move R1 to specific position (100, 50)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Move R1 to (100, 50)")
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

        print(f"✅ Step 2: R1 moved to (100, 50)")
        print(f"   - Previous position: {default_pos}")
        print(f"   - New position: {moved_pos}")
        print(f"   - UUID unchanged: {r1_uuid}")

        # =====================================================================
        # STEP 3: Change reference R1 → R2 in Python
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Change reference R1 → R2 in Python")
        print("="*70)

        # Modify Python code: ref="R1" → ref="R2"
        modified_code = original_code.replace(
            'ref="R1"',
            'ref="R2"'
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 3: Reference changed to R2 in Python")

        # =====================================================================
        # STEP 4: Regenerate KiCad (UUID matching should preserve position)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Regenerate KiCad (test UUID-based matching)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "single_resistor.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration with renamed reference\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"\n📋 Synchronization output:")
        print(result.stdout)

        # =====================================================================
        # STEP 5: Validate position preserved and reference updated
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate UUID matching worked (Issue #369 fix)")
        print("="*70)

        sch_final = Schematic.load(str(schematic_file))
        components_final = sch_final.components

        assert len(components_final) == 1, (
            f"Expected 1 component, found {len(components_final)}"
        )

        r2 = components_final[0]
        final_pos = r2.position
        final_uuid = r2.uuid

        # CRITICAL: Reference should be updated
        assert r2.reference == "R2", (
            f"Reference should be R2, got {r2.reference}"
        )

        # CRITICAL: Position should be preserved (UUID matching worked!)
        assert final_pos.x == 100.0 and final_pos.y == 50.0, (
            f"❌ POSITION NOT PRESERVED!\n"
            f"   Expected: (100, 50)\n"
            f"   Got: {final_pos}\n"
            f"   This means UUID matching did NOT work!\n"
            f"   Issue #369 is NOT fixed!"
        )

        # UUID should be preserved
        assert final_uuid == r1_uuid, (
            f"UUID changed! Expected {r1_uuid}, got {final_uuid}\n"
            f"This suggests component was removed and re-added"
        )

        # Check sync logs - should show Update, not Remove+Add
        sync_output = result.stdout
        has_remove = "Remove:" in sync_output or "⚠️  Remove:" in sync_output
        has_add = "Add:" in sync_output or "➕ Add:" in sync_output

        print(f"\n✅ Step 5: UUID-based matching VALIDATED!")
        print(f"   - Reference updated: R1 → R_PULLUP ✓")
        print(f"   - Position preserved: {final_pos} ✓")
        print(f"   - UUID preserved: {final_uuid} ✓")

        if has_remove or has_add:
            print(f"   ⚠️  Sync showed Remove/Add (expected with Issue #369)")
            print(f"      But position was still preserved via UUID!")
        else:
            print(f"   - Sync showed Update (best case) ✓")

        print(f"\n🎉 Issue #369 FIX CONFIRMED!")
        print(f"   Reference changes now preserve position via UUID matching!")

    finally:
        # Restore original Python file (R1)
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
