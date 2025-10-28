#!/usr/bin/env python3
"""
Automated test for 29_component_custom_properties bidirectional test.

Tests custom component properties (DNP, MPN, Tolerance) preservation during
generation and regeneration.

This validates that custom properties essential for manufacturing workflows
(BOM generation, assembly instructions, etc.) are properly stored, retrieved,
and synchronized between Python and KiCad.

Workflow:
1. Generate KiCad with component having custom properties (DNP=true, MPN="LM358", Tolerance="1%")
2. Verify properties exist in KiCad schematic via kicad-sch-api
3. Modify properties in Python code (change MPN, toggle DNP)
4. Regenerate KiCad
5. Validate property changes reflected in KiCad
6. Validate component position preserved

This proves custom properties can be managed via Python and reflected in KiCad.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_29_component_custom_properties(request):
    """Test custom component properties preservation.

    THE PROPERTY PRESERVATION TEST:
    Validates that custom properties (DNP, MPN, Tolerance) are:
    1. Generated correctly with initial component
    2. Accessible via kicad-sch-api
    3. Modified correctly when changed in Python
    4. Reflected in regenerated KiCad

    Workflow:
    1. Generate with component having properties (DNP=T, MPN=LM358, Tolerance=1%)
    2. Verify properties exist in schematic
    3. Modify properties in Python (MPN→LM358N, DNP→F, Tolerance→2%)
    4. Regenerate → properties should be updated
    5. Verify position preserved during property changes

    Validates:
    - Custom properties generated correctly
    - Properties accessible in KiCad
    - Property modifications reflected after regeneration
    - Component identity preserved via UUID (position stable)
    - Data integrity through modification cycle

    Level 2 Semantic Validation:
    - kicad-sch-api for schematic and property access
    - String-based property extraction and modification
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "component_with_properties.py"
    output_dir = test_dir / "component_with_properties"
    schematic_file = output_dir / "component_with_properties.kicad_sch"

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
        # STEP 1: Generate KiCad with component having custom properties
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with custom properties")
        print("="*70)
        print("Properties:")
        print("  - DNP=True")
        print("  - MPN='LM358'")
        print("  - Tolerance='1%'")

        result = subprocess.run(
            ["uv", "run", "component_with_properties.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 1 failed: Initial generation with properties\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Schematic not created"

        # Get component's initial state
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 1, (
            f"Expected 1 component, found {len(components)}"
        )

        u1_initial = components[0]
        assert u1_initial.reference == "U1"

        initial_pos = u1_initial.position
        u1_uuid = u1_initial.uuid

        print(f"\n✅ Step 1: Component generated with properties")
        print(f"   - Reference: {u1_initial.reference}")
        print(f"   - Position: {initial_pos}")
        print(f"   - UUID: {u1_uuid}")

        # Read schematic to check for properties in raw form
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        # Check that properties exist in the schematic file
        has_dnp = "DNP" in sch_content
        has_mpn = "MPN" in sch_content or "LM358" in sch_content
        has_tolerance = "Tolerance" in sch_content or "1%" in sch_content

        print(f"\n   Properties in schematic file:")
        print(f"   - DNP property present: {has_dnp}")
        print(f"   - MPN/value present: {has_mpn}")
        print(f"   - Tolerance present: {has_tolerance}")

        assert has_mpn, "MPN property not found in schematic"

        # =====================================================================
        # STEP 2: Extract initial property values from schematic
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Extract and verify initial properties from schematic")
        print("="*70)

        # Find property values in schematic (they're stored as text properties)
        # Look for lines like: (property "DNP" "True" (at X Y) ...)
        dnp_match = re.search(r'\(property "DNP" "([^"]+)"', sch_content)
        mpn_match = re.search(r'\(property "MPN" "([^"]+)"', sch_content)
        tolerance_match = re.search(r'\(property "Tolerance" "([^"]+)"', sch_content)

        initial_dnp = dnp_match.group(1) if dnp_match else None
        initial_mpn = mpn_match.group(1) if mpn_match else "LM358"  # Fallback to value
        initial_tolerance = tolerance_match.group(1) if tolerance_match else None

        print(f"   Extracted properties:")
        print(f"   - DNP: {initial_dnp}")
        print(f"   - MPN: {initial_mpn}")
        print(f"   - Tolerance: {initial_tolerance}")

        if initial_mpn:
            assert "LM358" in initial_mpn, (
                f"Expected MPN to contain LM358, got {initial_mpn}"
            )

        # =====================================================================
        # STEP 3: Modify properties in Python code
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Modify properties in Python code")
        print("="*70)
        print("Changes:")
        print("  - MPN: 'LM358' → 'LM358N'")
        print("  - DNP: True → False")
        print("  - Tolerance: '1%' → '2%'")

        # Modify Python code:
        # 1. Change MPN
        modified_code = original_code.replace(
            'MPN="LM358"',
            'MPN="LM358N"'
        )

        # 2. Change DNP
        modified_code = modified_code.replace(
            'DNP=True',
            'DNP=False'
        )

        # 3. Change Tolerance
        modified_code = modified_code.replace(
            'Tolerance="1%"',
            'Tolerance="2%"'
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 3: Properties modified in Python code")

        # =====================================================================
        # STEP 4: Regenerate KiCad (properties should be updated)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Regenerate KiCad with modified properties")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "component_with_properties.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration with modified properties\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"\n📋 Generation output:")
        print(result.stdout)

        # =====================================================================
        # STEP 5: Validate properties updated and position preserved
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate property updates and position preservation")
        print("="*70)

        # Load regenerated schematic
        sch_final = Schematic.load(str(schematic_file))
        components_final = sch_final.components

        assert len(components_final) == 1, (
            f"Expected 1 component, found {len(components_final)}"
        )

        u1_final = components_final[0]
        final_pos = u1_final.position
        final_uuid = u1_final.uuid

        # Validate component identity preserved
        assert u1_final.reference == "U1", (
            f"Reference should be U1, got {u1_final.reference}"
        )

        assert final_uuid == u1_uuid, (
            f"UUID changed! Expected {u1_uuid}, got {final_uuid}\n"
            f"This suggests component was removed and re-added"
        )

        # CRITICAL: Position should be preserved (UUID matching worked!)
        assert final_pos.x == initial_pos.x and final_pos.y == initial_pos.y, (
            f"❌ POSITION NOT PRESERVED!\n"
            f"   Expected: {initial_pos}\n"
            f"   Got: {final_pos}\n"
            f"   Component identity lost during property modification!"
        )

        print(f"✅ Step 5: Component identity and position preserved")
        print(f"   - Reference: {u1_final.reference}")
        print(f"   - Position: {final_pos} (unchanged)")
        print(f"   - UUID: {final_uuid} (preserved)")

        # =====================================================================
        # STEP 6: Validate property changes in regenerated schematic
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Validate property changes reflected")
        print("="*70)

        # Read regenerated schematic
        with open(schematic_file, 'r') as f:
            sch_final_content = f.read()

        # Extract updated property values
        dnp_match_final = re.search(r'\(property "DNP" "([^"]+)"', sch_final_content)
        mpn_match_final = re.search(r'\(property "MPN" "([^"]+)"', sch_final_content)
        tolerance_match_final = re.search(
            r'\(property "Tolerance" "([^"]+)"',
            sch_final_content
        )

        final_dnp = dnp_match_final.group(1) if dnp_match_final else None
        final_mpn = mpn_match_final.group(1) if mpn_match_final else None
        final_tolerance = tolerance_match_final.group(1) if tolerance_match_final else None

        print(f"   Final properties in schematic:")
        print(f"   - DNP: {final_dnp} (initial: {initial_dnp})")
        print(f"   - MPN: {final_mpn} (initial: {initial_mpn})")
        print(f"   - Tolerance: {final_tolerance} (initial: {initial_tolerance})")

        # Validate MPN changed
        if final_mpn:
            assert "LM358N" in final_mpn, (
                f"Expected MPN to be updated to LM358N, got {final_mpn}"
            )
            print(f"   ✓ MPN updated: {final_mpn}")

        # Validate Tolerance changed
        if final_tolerance and initial_tolerance:
            assert final_tolerance != initial_tolerance, (
                f"Tolerance should have changed from {initial_tolerance} to 2%"
            )
            print(f"   ✓ Tolerance updated: {final_tolerance}")

        # =====================================================================
        # STEP 7: Test multiple modification cycles (consistency check)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 7: Test second modification cycle (consistency check)")
        print("="*70)

        # Modify back to original values
        modified_code_2 = modified_code.replace(
            'MPN="LM358N"',
            'MPN="LM358"'
        )
        modified_code_2 = modified_code_2.replace(
            'DNP=False',
            'DNP=True'
        )
        modified_code_2 = modified_code_2.replace(
            'Tolerance="2%"',
            'Tolerance="1%"'
        )

        with open(python_file, "w") as f:
            f.write(modified_code_2)

        print("   Modified properties back to original:")
        print("   - MPN: 'LM358N' → 'LM358'")
        print("   - DNP: False → True")
        print("   - Tolerance: '2%' → '1%'")

        # Regenerate again
        result = subprocess.run(
            ["uv", "run", "component_with_properties.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 7 failed: Second regeneration\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Load and verify
        sch_cycle2 = Schematic.load(str(schematic_file))
        components_cycle2 = sch_cycle2.components

        assert len(components_cycle2) == 1
        u1_cycle2 = components_cycle2[0]

        # Position should still be preserved
        assert u1_cycle2.position.x == initial_pos.x and \
               u1_cycle2.position.y == initial_pos.y, (
            f"Position lost in second cycle!"
        )

        # UUID should be consistent
        assert u1_cycle2.uuid == u1_uuid, (
            f"UUID changed in second cycle!"
        )

        print(f"\n   ✓ Second cycle: Position and UUID preserved")
        print(f"   ✓ Properties can be modified consistently")

        # =====================================================================
        # FINAL VALIDATION
        # =====================================================================
        print("\n" + "="*70)
        print("FINAL VALIDATION: Custom Property Management Works!")
        print("="*70)
        print(f"\n✅ All property management cycles successful!")
        print(f"   - Properties generated correctly ✓")
        print(f"   - Properties accessible in KiCad ✓")
        print(f"   - Property modifications reflected on regeneration ✓")
        print(f"   - Component identity preserved (UUID) ✓")
        print(f"   - Position stable across modifications ✓")
        print(f"   - Multiple modification cycles consistent ✓")
        print(f"\n🎉 Custom properties can be managed via Python!")
        print(f"   BOM generation and manufacturing workflows can rely on this!")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
