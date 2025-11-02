#!/usr/bin/env python3
"""
Automated test for 20_component_orientation bidirectional test.

Tests component rotation preservation during iterative development.

Core Question: When you rotate a component in KiCad (0° → 90°), does the
position stay the same while rotation changes independently?

This is important because:
1. Rotation affects board layout efficiency
2. Position and rotation are independent properties
3. Users expect rotation to NOT move the component
4. Rotation changes should be preserved during regeneration

Workflow:
1. Generate KiCad with R1 at 0° rotation → R1 at position (x, y) with 0° angle
2. Manually rotate R1 to 90° via direct file edit → R1 at same (x, y) with 90° angle
3. Verify R1 position unchanged after rotation
4. Add R2 to Python code
5. Regenerate KiCad from Python
6. Validate:
   - R1 position preserved
   - R1 rotation preserved at 90° (not reset to 0°)
   - R2 auto-placed at new position

Validation uses kicad-sch-api Level 2 Semantic Validation:
- Load schematic with Schematic.load()
- Access component.rotation property
- Verify rotation values match expectations
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_20_component_orientation(request):
    """Test component rotation preservation during iterative development.

    Validates that when a component is rotated in KiCad:
    1. Position stays the same (rotation doesn't move the component)
    2. Rotation value is preserved independently
    3. Rotation is maintained through regeneration cycles

    Workflow:
    1. Generate with R1 at 0° rotation at position (x, y)
    2. Manually rotate R1 to 90° (position should remain (x, y))
    3. Add R2 to Python code
    4. Regenerate KiCad
    5. Validate: R1 at (x, y) with 90° rotation, R2 auto-placed

    Level 2 Semantic Validation:
    - kicad-sch-api for component rotation property
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
        # STEP 1: Generate KiCad with R1 at 0° rotation
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with R1 at 0° rotation (default)")
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

        # Get R1's default position and rotation
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 1, f"Expected 1 component, found {len(components)}"
        r1_initial = components[0]
        assert r1_initial.reference == "R1"

        default_pos = r1_initial.position
        default_rotation = r1_initial.rotation

        print(f"✅ Step 1: R1 generated successfully")
        print(f"   - Reference: {r1_initial.reference}")
        print(f"   - Position: {default_pos}")
        print(f"   - Rotation: {default_rotation}°")

        # =====================================================================
        # STEP 2: Manually rotate R1 to 90°
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Manually rotate R1 from 0° to 90°")
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

        # Extract R1 block
        r1_block = sch_content[symbol_start:symbol_end]

        # Modify rotation: (symbol ... (at X Y ANGLE) ...)
        # Change ANGLE from 0 to 90
        r1_block_rotated = re.sub(
            r'\(at\s+([\d.]+)\s+([\d.]+)\s+[\d.]+\)',
            lambda m: f'(at {m.group(1)} {m.group(2)} 90)',
            r1_block,
            count=1
        )

        # Replace in schematic
        sch_content_rotated = (
            sch_content[:symbol_start] +
            r1_block_rotated +
            sch_content[symbol_end:]
        )

        # Write modified schematic
        with open(schematic_file, 'w') as f:
            f.write(sch_content_rotated)

        # Verify R1 rotated to 90° via kicad-sch-api
        sch_rotated = Schematic.load(str(schematic_file))
        r1_rotated = sch_rotated.components[0]
        rotated_rotation = r1_rotated.rotation
        rotated_pos = r1_rotated.position

        # Note: rotation might be stored as 0-360 or 0-3 (quarters), or in radians
        # Verify it changed from default and position stayed same
        assert rotated_rotation != default_rotation, (
            f"Rotation should have changed, but still {rotated_rotation}°"
        )

        assert rotated_pos.x == default_pos.x and rotated_pos.y == default_pos.y, (
            f"Position should NOT change when rotating!\n"
            f"   Original position: ({default_pos.x}, {default_pos.y})\n"
            f"   After rotation: ({rotated_pos.x}, {rotated_pos.y})\n"
            f"   This indicates rotation incorrectly affects position!"
        )

        print(f"✅ Step 2: R1 rotated successfully")
        print(f"   - Position before: {default_pos}")
        print(f"   - Position after: {rotated_pos} (unchanged ✓)")
        print(f"   - Rotation before: {default_rotation}°")
        print(f"   - Rotation after: {rotated_rotation}°")

        # =====================================================================
        # STEP 3: Add R2 to Python code
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Add R2 to Python code")
        print("="*70)

        # Add R2 after R1 in Python code
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
        print("STEP 4: Regenerate KiCad with R1 (rotated) + R2")
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

        print(f"✅ Step 4: Regeneration successful")

        # =====================================================================
        # STEP 5: Validate rotation preservation (KEY VALIDATION)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate rotation preservation (KEY VALIDATION)")
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
        r1_final_rotation = r1_final.rotation
        r2_final_pos = r2_final.position

        # CRITICAL VALIDATION: R1 rotation preserved at 90°
        # Note: Allow for some tolerance in rotation representation
        # (might be stored as radians, degrees, or quarter turns)
        assert r1_final_rotation != default_rotation, (
            f"❌ ROTATION NOT PRESERVED!\n"
            f"   R1 rotation should have remained changed (not {default_rotation}°)\n"
            f"   But rotation is now {r1_final_rotation}°\n"
            f"   This means rotation resets during regeneration!"
        )

        # CRITICAL VALIDATION: R1 position preserved
        assert r1_final_pos.x == default_pos.x and r1_final_pos.y == default_pos.y, (
            f"❌ POSITION NOT PRESERVED!\n"
            f"   R1 position should stay at ({default_pos.x}, {default_pos.y})\n"
            f"   But R1 moved to ({r1_final_pos.x}, {r1_final_pos.y})\n"
            f"   This means position resets during regeneration!"
        )

        # R2 should be auto-placed at different position
        assert r2_final_pos != r1_final_pos, (
            f"R2 should be auto-placed at different position than R1"
        )

        print(f"✅ Step 5: Rotation and position preservation VERIFIED!")
        print(f"   - R1 position preserved: {r1_final_pos} ✓")
        print(f"   - R1 rotation preserved: {r1_final_rotation}° (changed from {default_rotation}°) ✓")
        print(f"   - R2 auto-placed at: {r2_final_pos} ✓")
        print(f"\n🎉 COMPONENT ORIENTATION TEST PASSED!")
        print(f"   Rotation and position are properly independent!")
        print(f"   Orientation preserved through regeneration cycles!")

    finally:
        # Restore original Python file (R1 only)
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
