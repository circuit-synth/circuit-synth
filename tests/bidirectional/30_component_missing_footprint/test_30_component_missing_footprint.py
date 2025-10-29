#!/usr/bin/env python3
"""
Automated test for 30_component_missing_footprint bidirectional test.

Tests graceful handling of components without footprint assignment.

This validates that circuit-synth properly handles the very common real-world
scenario where components are defined during early design WITHOUT footprint
information (because footprint choices haven't been decided yet).

Workflow:
1. Generate KiCad with component having empty footprint
2. Verify component appears in schematic without footprint field
3. Verify component position is assigned and can be adjusted
4. Add footprint assignment in Python code
5. Regenerate KiCad
6. Validate:
   - Footprint now appears in schematic
   - Component position preserved
   - Component remains valid for PCB design

This proves circuit-synth supports real iterative design workflows
where metadata is added incrementally, not all upfront.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_30_component_missing_footprint_graceful_handling(request):
    """Test graceful handling of components without footprint assignment.

    CRITICAL SCENARIO:
    In real circuit design, developers often start with just symbols
    (no footprints) because they haven't decided which package to use yet.
    This test validates that circuit-synth handles this gracefully.

    Workflow:
    1. Generate with R1 but footprint="" (no footprint assignment)
    2. Verify component appears in schematic without footprint field
    3. Verify position is assigned
    4. Add footprint in Python: footprint="Resistor_SMD:R_0603_1608Metric"
    5. Regenerate
    6. Validate:
       - Footprint now appears in schematic
       - Position preserved
       - No errors or duplicates

    Level 2 Semantic Validation:
    - kicad-sch-api for component.footprint property validation
    - Verify empty/None footprint initially, populated after update
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "component_no_footprint.py"
    output_dir = test_dir / "component_no_footprint"
    schematic_file = output_dir / "component_no_footprint.kicad_sch"

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
        # STEP 1: Generate KiCad with component having no footprint
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with component (footprint=\"\")")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "component_no_footprint.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 1 failed: Initial generation without footprint\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Schematic not created"

        # Get R1's initial state (no footprint)
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 1, (
            f"Expected 1 component, got {len(components)}"
        )

        r1_initial = components[0]
        assert r1_initial.reference == "R1", (
            f"Expected reference R1, got {r1_initial.reference}"
        )

        initial_pos = r1_initial.position
        initial_footprint = r1_initial.footprint
        r1_uuid = r1_initial.uuid

        print(f"✅ Step 1: R1 generated without footprint")
        print(f"   - Reference: {r1_initial.reference}")
        print(f"   - Footprint: '{initial_footprint}' (empty/None)")
        print(f"   - Position: {initial_pos}")
        print(f"   - UUID: {r1_uuid}")

        # Verify footprint is indeed missing/empty
        assert initial_footprint is None or initial_footprint == "", (
            f"❌ Footprint should be empty/None initially, got: '{initial_footprint}'"
        )

        # =====================================================================
        # STEP 2: Manually move component in KiCad schematic (simulate user adjustment)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Manually move R1 to (80, 40) (simulate user layout)")
        print("="*70)

        # Read schematic file
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        # Find R1 symbol block
        r1_ref_pos = sch_content.find('(property "Reference" "R1"')
        assert r1_ref_pos != -1, "Could not find R1 in schematic"

        # Find symbol block start
        symbol_start = sch_content.rfind('(symbol', 0, r1_ref_pos)
        assert symbol_start != -1, "Could not find symbol block start"

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

        # Extract and modify R1 block to move to (80, 40)
        r1_block = sch_content[symbol_start:symbol_end]

        # Modify position: (symbol ... (at X Y ANGLE) ...)
        r1_block_moved = re.sub(
            r'\(at\s+[\d.]+\s+[\d.]+\s+[\d.]+\)',
            '(at 80 40 0)',
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

        # Verify R1 moved to (80, 40)
        sch_moved = Schematic.load(str(schematic_file))
        r1_moved = sch_moved.components[0]
        moved_pos = r1_moved.position

        assert moved_pos.x == 80.0 and moved_pos.y == 40.0, (
            f"R1 should be at (80, 40), got {moved_pos}"
        )

        print(f"✅ Step 2: R1 moved to (80, 40)")
        print(f"   - Previous position: {initial_pos}")
        print(f"   - New position: {moved_pos}")
        print(f"   - Footprint still empty: '{r1_moved.footprint}'")

        # =====================================================================
        # STEP 3: Add footprint assignment in Python code
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Add footprint in Python code")
        print("="*70)

        # Modify Python code: footprint="" → footprint="Resistor_SMD:R_0603_1608Metric"
        modified_code = original_code.replace(
            'footprint="",',
            'footprint="Resistor_SMD:R_0603_1608Metric",'
        )

        # Verify we actually made the change
        assert modified_code != original_code, (
            "Failed to modify Python code - footprint not added"
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 3: Footprint added to Python code")
        print(f"   - New footprint: Resistor_SMD:R_0603_1608Metric")

        # =====================================================================
        # STEP 4: Regenerate KiCad (footprint should now appear)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Regenerate KiCad (with footprint now assigned)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "component_no_footprint.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration with footprint\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"\n📋 Synchronization output:")
        print(result.stdout)

        # =====================================================================
        # STEP 5: Validate footprint now appears and position preserved
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate footprint added and position preserved")
        print("="*70)

        sch_final = Schematic.load(str(schematic_file))
        components_final = sch_final.components

        assert len(components_final) == 1, (
            f"Expected 1 component, found {len(components_final)}"
        )

        r1_final = components_final[0]
        final_footprint = r1_final.footprint
        final_pos = r1_final.position
        final_uuid = r1_final.uuid

        # CRITICAL: Footprint should now be populated
        assert final_footprint is not None and final_footprint != "", (
            f"❌ Footprint should be set, got: '{final_footprint}'"
        )

        assert "R_0603" in final_footprint or "R_0603_1608Metric" in final_footprint, (
            f"❌ Footprint should contain R_0603, got: '{final_footprint}'"
        )

        # CRITICAL: Position should be preserved (not reset to default!)
        assert final_pos.x == 80.0 and final_pos.y == 40.0, (
            f"❌ POSITION NOT PRESERVED!\n"
            f"   Expected: (80, 40)\n"
            f"   Got: {final_pos}\n"
            f"   This means manual position was lost when footprint added!"
        )

        # UUID should be preserved
        assert final_uuid == r1_uuid, (
            f"UUID changed! Expected {r1_uuid}, got {final_uuid}\n"
            f"This suggests component was removed and re-added"
        )

        # Reference should remain unchanged
        assert r1_final.reference == "R1", (
            f"Reference should still be R1, got {r1_final.reference}"
        )

        print(f"\n✅ Step 5: VALIDATION COMPLETE!")
        print(f"   - Footprint now populated: {final_footprint} ✓")
        print(f"   - Position preserved: {final_pos} ✓")
        print(f"   - UUID preserved: {final_uuid} ✓")
        print(f"   - Reference unchanged: {r1_final.reference} ✓")

        print(f"\n🎉 GRACEFUL HANDLING CONFIRMED!")
        print(f"   Components without footprints are handled correctly!")
        print(f"   Footprints can be added later without losing position!")
        print(f"   This validates real iterative design workflows!")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
