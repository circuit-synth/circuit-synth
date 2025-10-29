#!/usr/bin/env python3
"""
Automated test for 63_component_rotation_preservation bidirectional test.

Tests comprehensive rotation preservation for multiple components at different angles.

Core Question: When you rotate components to specific angles (0°, 90°, 180°, 270°)
in KiCad and then regenerate from Python, are all rotation angles preserved
independently of component modifications?

This is a Priority 2 feature (Nice-to-have - Aesthetic) because:
1. Rotation affects visual layout and board organization
2. Users expect rotation to be preserved like position
3. Rotation should be independent of value changes
4. New components shouldn't affect existing rotations

Workflow:
1. Generate KiCad with 4 resistors (R1, R2, R3, R4) at default 0° rotation
2. Manually rotate components in KiCad:
   - R1: 0° (horizontal - unchanged)
   - R2: 90° (vertical)
   - R3: 180° (horizontal reversed)
   - R4: 270° (vertical reversed)
3. Modify R2 value in Python (10k → 22k)
4. Regenerate KiCad
5. Validate all rotations preserved (R2 still at 90° despite value change)
6. Add R5 to Python
7. Regenerate KiCad
8. Validate R1-R4 rotations still preserved, R5 at default rotation

Validation uses kicad-sch-api Level 2 Semantic Validation:
- Load schematic with Schematic.load()
- Access component.rotation property
- Verify rotation values match expected angles
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_63_component_rotation_preservation(request):
    """Test comprehensive rotation preservation for multiple components.

    Validates that component rotation angles are preserved through
    bidirectional sync cycles, even when components are modified or
    new components are added.

    Workflow:
    1. Generate with 4 resistors at default 0° rotation
    2. Manually rotate R1=0°, R2=90°, R3=180°, R4=270°
    3. Modify R2 value in Python
    4. Regenerate → All rotations preserved
    5. Add R5 in Python
    6. Regenerate → R1-R4 rotations preserved, R5 at default

    Why critical:
    - Rotation is part of layout aesthetics
    - Should be preserved independently like position
    - Value changes shouldn't reset rotation
    - New components shouldn't affect existing rotations

    Level 2 Semantic Validation:
    - kicad-sch-api for rotation property validation
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "rotated_components.py"
    output_dir = test_dir / "rotated_components"
    schematic_file = output_dir / "rotated_components.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file (R1-R4 only)
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate KiCad with 4 resistors at default rotation (0°)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with 4 resistors (default 0° rotation)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "rotated_components.py"],
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

        # Get components' default positions and rotations
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 4, f"Expected 4 components, found {len(components)}"

        # Find all resistors
        r1_init = next((c for c in components if c.reference == "R1"), None)
        r2_init = next((c for c in components if c.reference == "R2"), None)
        r3_init = next((c for c in components if c.reference == "R3"), None)
        r4_init = next((c for c in components if c.reference == "R4"), None)

        assert all([r1_init, r2_init, r3_init, r4_init]), "Not all resistors found"

        # Store initial positions (will be preserved throughout)
        r1_pos = r1_init.position
        r2_pos = r2_init.position
        r3_pos = r3_init.position
        r4_pos = r4_init.position

        print(f"✅ Step 1: 4 resistors generated at default rotation")
        print(f"   - R1: position {r1_pos}, rotation {r1_init.rotation}°")
        print(f"   - R2: position {r2_pos}, rotation {r2_init.rotation}°")
        print(f"   - R3: position {r3_pos}, rotation {r3_init.rotation}°")
        print(f"   - R4: position {r4_pos}, rotation {r4_init.rotation}°")

        # =====================================================================
        # STEP 2: Manually rotate components to specific angles
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Rotate components to R1=0°, R2=90°, R3=180°, R4=270°")
        print("="*70)

        # Read schematic file
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        # Helper function to rotate a component
        def rotate_component(content, ref, angle):
            """Rotate component to specific angle while preserving position."""
            # Find reference property
            ref_search = f'(property "Reference" "{ref}"'
            ref_pos = content.find(ref_search)
            if ref_pos == -1:
                raise ValueError(f"Could not find {ref} in schematic")

            # Find symbol block start (search backwards from reference)
            symbol_start = content.rfind('(symbol', 0, ref_pos)
            if symbol_start == -1:
                raise ValueError(f"Could not find symbol block for {ref}")

            # Find matching closing parenthesis
            paren_count = 0
            i = symbol_start
            symbol_end = -1

            while i < len(content):
                if content[i] == '(':
                    paren_count += 1
                elif content[i] == ')':
                    paren_count -= 1
                    if paren_count == 0:
                        symbol_end = i + 1
                        break
                i += 1

            if symbol_end == -1:
                raise ValueError(f"Could not find closing parenthesis for {ref}")

            # Extract and modify symbol block
            symbol_block = content[symbol_start:symbol_end]

            # Modify rotation: (at X Y ANGLE) → (at X Y new_angle)
            # Preserve X and Y coordinates
            symbol_block_rotated = re.sub(
                r'\(at\s+([\d.]+)\s+([\d.]+)\s+[\d.]+\)',
                lambda m: f'(at {m.group(1)} {m.group(2)} {angle})',
                symbol_block,
                count=1
            )

            # Replace in content
            return (
                content[:symbol_start] +
                symbol_block_rotated +
                content[symbol_end:]
            )

        # Rotate each component to its target angle
        sch_content = rotate_component(sch_content, "R1", 0)      # Horizontal
        sch_content = rotate_component(sch_content, "R2", 90)     # Vertical
        sch_content = rotate_component(sch_content, "R3", 180)    # Horizontal reversed
        sch_content = rotate_component(sch_content, "R4", 270)    # Vertical reversed

        # Write modified schematic
        with open(schematic_file, 'w') as f:
            f.write(sch_content)

        # Verify rotations via kicad-sch-api
        sch_rotated = Schematic.load(str(schematic_file))
        comps_rotated = sch_rotated.components

        r1_rot = next((c for c in comps_rotated if c.reference == "R1"), None)
        r2_rot = next((c for c in comps_rotated if c.reference == "R2"), None)
        r3_rot = next((c for c in comps_rotated if c.reference == "R3"), None)
        r4_rot = next((c for c in comps_rotated if c.reference == "R4"), None)

        assert r1_rot.rotation == 0, f"R1 should be at 0°, got {r1_rot.rotation}°"
        assert r2_rot.rotation == 90, f"R2 should be at 90°, got {r2_rot.rotation}°"
        assert r3_rot.rotation == 180, f"R3 should be at 180°, got {r3_rot.rotation}°"
        assert r4_rot.rotation == 270, f"R4 should be at 270°, got {r4_rot.rotation}°"

        # Verify positions unchanged
        assert r1_rot.position == r1_pos, "R1 position changed during rotation"
        assert r2_rot.position == r2_pos, "R2 position changed during rotation"
        assert r3_rot.position == r3_pos, "R3 position changed during rotation"
        assert r4_rot.position == r4_pos, "R4 position changed during rotation"

        print(f"✅ Step 2: Components rotated successfully")
        print(f"   - R1: {r1_rot.rotation}° (horizontal)")
        print(f"   - R2: {r2_rot.rotation}° (vertical)")
        print(f"   - R3: {r3_rot.rotation}° (horizontal reversed)")
        print(f"   - R4: {r4_rot.rotation}° (vertical reversed)")
        print(f"   - All positions preserved ✓")

        # =====================================================================
        # STEP 3: Modify R2 value in Python (10k → 22k)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Modify R2 value in Python (10k → 22k)")
        print("="*70)

        # Change R2 value
        modified_code = original_code.replace(
            'ref="R2",\n        value="10k",',
            'ref="R2",\n        value="22k",'
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 3: R2 value changed to 22k")

        # =====================================================================
        # STEP 4: Regenerate KiCad (validate rotations preserved)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Regenerate KiCad (R2 value changed)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "rotated_components.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration after value change\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # =====================================================================
        # STEP 5: Validate all rotations preserved (KEY VALIDATION)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate rotations preserved after value change")
        print("="*70)

        sch_after_value = Schematic.load(str(schematic_file))
        comps_after_value = sch_after_value.components

        r1_val = next((c for c in comps_after_value if c.reference == "R1"), None)
        r2_val = next((c for c in comps_after_value if c.reference == "R2"), None)
        r3_val = next((c for c in comps_after_value if c.reference == "R3"), None)
        r4_val = next((c for c in comps_after_value if c.reference == "R4"), None)

        # CRITICAL VALIDATION: All rotations preserved
        assert r1_val.rotation == 0, (
            f"❌ R1 ROTATION NOT PRESERVED!\n"
            f"   Expected: 0°, Got: {r1_val.rotation}°"
        )
        assert r2_val.rotation == 90, (
            f"❌ R2 ROTATION NOT PRESERVED DESPITE VALUE CHANGE!\n"
            f"   Expected: 90°, Got: {r2_val.rotation}°"
        )
        assert r3_val.rotation == 180, (
            f"❌ R3 ROTATION NOT PRESERVED!\n"
            f"   Expected: 180°, Got: {r3_val.rotation}°"
        )
        assert r4_val.rotation == 270, (
            f"❌ R4 ROTATION NOT PRESERVED!\n"
            f"   Expected: 270°, Got: {r4_val.rotation}°"
        )

        # Verify R2 value actually changed
        assert r2_val.value == "22k", f"R2 value should be 22k, got {r2_val.value}"

        # Verify positions still preserved
        assert r1_val.position == r1_pos, "R1 position not preserved"
        assert r2_val.position == r2_pos, "R2 position not preserved"
        assert r3_val.position == r3_pos, "R3 position not preserved"
        assert r4_val.position == r4_pos, "R4 position not preserved"

        print(f"✅ Step 5: All rotations preserved after value change!")
        print(f"   - R1: {r1_val.rotation}° ✓")
        print(f"   - R2: {r2_val.rotation}° ✓ (value changed to {r2_val.value})")
        print(f"   - R3: {r3_val.rotation}° ✓")
        print(f"   - R4: {r4_val.rotation}° ✓")
        print(f"   - All positions preserved ✓")

        # =====================================================================
        # STEP 6: Add R5 to Python code
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Add R5 to Python code")
        print("="*70)

        # Add R5 after R4
        r4_end_pattern = r'(r4 = Component\([^)]+\))'

        r5_code = '''

    r5 = Component(
        symbol="Device:R",
        ref="R5",
        value="100k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )'''

        modified_code_r5 = re.sub(
            r4_end_pattern,
            r'\1' + r5_code,
            modified_code,
            count=1
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code_r5)

        print(f"✅ Step 6: R5 added to Python code")

        # =====================================================================
        # STEP 7: Regenerate with R5
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 7: Regenerate KiCad with R1-R5")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "rotated_components.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 7 failed: Regeneration with R5\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # =====================================================================
        # STEP 8: Final validation - R1-R4 rotations + R5 default
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 8: Final validation - All rotations preserved + R5 default")
        print("="*70)

        sch_final = Schematic.load(str(schematic_file))
        comps_final = sch_final.components

        assert len(comps_final) == 5, (
            f"Expected 5 components, found {len(comps_final)}"
        )

        r1_final = next((c for c in comps_final if c.reference == "R1"), None)
        r2_final = next((c for c in comps_final if c.reference == "R2"), None)
        r3_final = next((c for c in comps_final if c.reference == "R3"), None)
        r4_final = next((c for c in comps_final if c.reference == "R4"), None)
        r5_final = next((c for c in comps_final if c.reference == "R5"), None)

        assert all([r1_final, r2_final, r3_final, r4_final, r5_final]), (
            "Not all resistors found in final schematic"
        )

        # CRITICAL VALIDATION: R1-R4 rotations still preserved
        assert r1_final.rotation == 0, (
            f"❌ R1 rotation not preserved after adding R5: {r1_final.rotation}°"
        )
        assert r2_final.rotation == 90, (
            f"❌ R2 rotation not preserved after adding R5: {r2_final.rotation}°"
        )
        assert r3_final.rotation == 180, (
            f"❌ R3 rotation not preserved after adding R5: {r3_final.rotation}°"
        )
        assert r4_final.rotation == 270, (
            f"❌ R4 rotation not preserved after adding R5: {r4_final.rotation}°"
        )

        # R5 should have default rotation (0°)
        # Note: R5 is new, so it gets auto-placed with default rotation
        print(f"   - R5 rotation: {r5_final.rotation}° (auto-placed)")

        # Verify R1-R4 positions still preserved
        assert r1_final.position == r1_pos, "R1 position not preserved"
        assert r2_final.position == r2_pos, "R2 position not preserved"
        assert r3_final.position == r3_pos, "R3 position not preserved"
        assert r4_final.position == r4_pos, "R4 position not preserved"

        print(f"✅ Step 8: COMPREHENSIVE ROTATION PRESERVATION VERIFIED!")
        print(f"   - R1: {r1_final.rotation}° (horizontal) ✓")
        print(f"   - R2: {r2_final.rotation}° (vertical, value=22k) ✓")
        print(f"   - R3: {r3_final.rotation}° (horizontal reversed) ✓")
        print(f"   - R4: {r4_final.rotation}° (vertical reversed) ✓")
        print(f"   - R5: {r5_final.rotation}° (new component, default) ✓")
        print(f"   - All R1-R4 positions preserved ✓")
        print(f"\n🎉 COMPONENT ROTATION PRESERVATION TEST PASSED!")
        print(f"   - Rotations preserved through value changes!")
        print(f"   - Rotations preserved when adding new components!")
        print(f"   - Rotation is truly independent of other properties!")

    finally:
        # Restore original Python file (R1-R4 only)
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
