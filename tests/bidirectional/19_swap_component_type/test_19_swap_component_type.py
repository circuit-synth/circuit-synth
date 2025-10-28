#!/usr/bin/env python3
"""
Automated test for 27_swap_component_type bidirectional test.

Tests component symbol type change with UUID-based matching.

LIMITATION: This test is marked as XFAIL because the synchronizer does not
support changing component library symbols (lib_id). While the Python code is
changed (Device:R → Device:C), the KiCad schematic does not reflect this change.
Fixing this limitation would require removing the old component and adding a new
one, which could break position preservation and UUID matching.

Workflow:
1. Generate KiCad with R1 (Device:R - resistor) at default position
2. Move R1 to specific position (100, 50)
3. Change symbol Device:R → Device:C (resistor → capacitor) in Python code
4. Keep reference as "R1" (unchanged)
5. Regenerate KiCad
6. EXPECTED (but doesn't work): Component shows capacitor symbol (not resistor)
7. What actually happens: Component still shows resistor symbol

This test documents the known limitation with symbol type changes during
design iteration.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.xfail(
    reason=(
        "Synchronizer does not support changing component library symbols (lib_id). "
        "Changing Device:R to Device:C in Python does not update the schematic. "
        "This would require removing the old component and adding a new one, which "
        "could break position preservation and UUID matching."
    )
)
def test_19_swap_component_type_resistor_to_capacitor(request):
    """Test symbol type change (Device:R → Device:C) with position preservation.

    KNOWN LIMITATION - MARKED XFAIL:
    This test documents a known limitation of the synchronizer: changing a
    component's library symbol (lib_id) is not supported. While you can change
    the symbol in Python code, the generated KiCad schematic will not reflect
    this change.

    Expected behavior (not implemented):
    - Changing Device:R → Device:C in Python should update the symbol in KiCad
    - Position and reference should be preserved via UUID-based matching
    - The component should be updated in-place, not removed and re-added

    Why this is difficult to implement:
    - Changing a symbol requires removing the old component instance and creating
      a new one in KiCad
    - UUID-based matching expects the component to already exist in the schematic
    - Simply updating the lib_id without proper removal/addition can cause issues
    - Position preservation and UUID matching could be broken during this process

    Workflow (attempted but fails):
    1. Generate with R1 (Device:R) → auto-placed position
    2. Move R1 to (100, 50)
    3. Change symbol Device:R → Device:C in Python (keep ref="R1")
    4. Regenerate → position and reference should be preserved
       ❌ But symbol doesn't actually change - stays as Device:R

    Level 2 Semantic Validation:
    - kicad-sch-api for symbol type, reference, position, and UUID validation
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

    # Read original Python file (Device:R with ref="R1")
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate KiCad with R1 (resistor - Device:R)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with R1 (Device:R - resistor)")
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

        # Get R1's default position and verify it's a resistor
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 1
        r1_initial = components[0]
        assert r1_initial.reference == "R1"

        # Verify it's a resistor symbol (Device:R)
        lib_id_str = str(r1_initial.lib_id)
        assert "R" in lib_id_str or "Resistor" in lib_id_str, (
            f"Expected resistor symbol, got: {lib_id_str}"
        )

        default_pos = r1_initial.position
        r1_uuid = r1_initial.uuid

        print(f"✅ Step 1: R1 generated (Device:R)")
        print(f"   - Reference: {r1_initial.reference}")
        print(f"   - Symbol: {r1_initial.lib_id}")
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
        # STEP 3: Change symbol Device:R → Device:C in Python
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Change symbol Device:R → Device:C in Python")
        print("="*70)

        # Modify Python code: symbol="Device:R" → symbol="Device:C"
        modified_code = original_code.replace(
            'symbol="Device:R"',
            'symbol="Device:C"'
        )

        # Verify the replacement happened
        assert 'symbol="Device:C"' in modified_code, (
            "Failed to replace Device:R with Device:C in Python code"
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 3: Symbol changed to Device:C in Python")
        print(f"   - From: symbol=\"Device:R\" (resistor)")
        print(f"   - To: symbol=\"Device:C\" (capacitor)")
        print(f"   - Reference: R1 (unchanged)")

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
            f"Step 4 failed: Regeneration with changed symbol\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"\n📋 Synchronization output:")
        print(result.stdout)

        # =====================================================================
        # STEP 5: Validate symbol changed and position/reference preserved
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate UUID matching worked (symbol type change)")
        print("="*70)

        sch_final = Schematic.load(str(schematic_file))
        components_final = sch_final.components

        assert len(components_final) == 1, (
            f"Expected 1 component, found {len(components_final)}"
        )

        c1 = components_final[0]
        final_pos = c1.position
        final_uuid = c1.uuid
        final_symbol = c1.lib_id

        # CRITICAL: Reference should STILL be R1 (not changed!)
        assert c1.reference == "R1", (
            f"❌ REFERENCE CHANGED!\n"
            f"   Expected: R1\n"
            f"   Got: {c1.reference}\n"
            f"   Symbol changes should NOT change reference!"
        )

        # CRITICAL: Symbol should be capacitor (Device:C)
        lib_id_str = str(final_symbol)
        assert "C" in lib_id_str or "Capacitor" in lib_id_str, (
            f"❌ SYMBOL NOT CHANGED!\n"
            f"   Expected: Device:C (capacitor)\n"
            f"   Got: {final_symbol}\n"
            f"   Symbol change did NOT work!"
        )

        # CRITICAL: Position should be preserved (UUID matching worked!)
        assert final_pos.x == 100.0 and final_pos.y == 50.0, (
            f"❌ POSITION NOT PRESERVED!\n"
            f"   Expected: (100, 50)\n"
            f"   Got: {final_pos}\n"
            f"   This means UUID matching did NOT work!\n"
            f"   Symbol change treated as Remove+Add, not Update!"
        )

        # UUID should be preserved
        assert final_uuid == r1_uuid, (
            f"❌ UUID CHANGED!\n"
            f"   Expected: {r1_uuid}\n"
            f"   Got: {final_uuid}\n"
            f"   This suggests component was removed and re-added"
        )

        # Check sync logs - should show Update, not Remove+Add
        sync_output = result.stdout
        has_remove = "Remove:" in sync_output or "⚠️  Remove:" in sync_output
        has_add = "Add:" in sync_output or "➕ Add:" in sync_output

        print(f"\n✅ Step 5: Symbol type change VALIDATED!")
        print(f"   - Symbol changed: Device:R → Device:C ✓")
        print(f"   - Reference preserved: R1 (unchanged) ✓")
        print(f"   - Position preserved: {final_pos} ✓")
        print(f"   - UUID preserved: {final_uuid} ✓")
        print(f"   - Symbol string: {final_symbol}")

        if has_remove or has_add:
            print(f"   ⚠️  Sync showed Remove/Add")
            print(f"      But position was still preserved via UUID!")
        else:
            print(f"   - Sync showed Update (best case) ✓")

        print(f"\n🎉 Symbol Type Change SUCCESSFUL!")
        print(f"   Resistor (Device:R) changed to Capacitor (Device:C)")
        print(f"   Position and reference preserved via UUID matching!")

    finally:
        # Restore original Python file (Device:R)
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
