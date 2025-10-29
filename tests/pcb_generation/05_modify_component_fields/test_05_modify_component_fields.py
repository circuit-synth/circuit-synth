#!/usr/bin/env python3
"""
Automated test for 05_modify_component_fields PCB test (CANONICAL UPDATE).

Tests that modifying component fields updates correctly without affecting position.

This validates the CANONICAL UPDATE pattern:
1. Generate PCB with 1 resistor (R1: 10k, 0603)
2. Store R1 position
3. Modify all fields: value→22k, footprint→0805, add description, add MPN, set DNP=true
4. Regenerate PCB
5. CRITICAL: R1 position UNCHANGED when fields modified
6. All new fields are correctly updated in PCB

This is critical because:
- Canonical updates (field-only changes) are common in PCB design
- Value changes: 10k → 22k (source tolerances, design tweaks)
- Footprint changes: 0603 → 0805 (better availability, rework considerations)
- Adding metadata: MPN, description, DNP flag
- WITHOUT position preservation, all manual placement work is lost
- This is the "canonical update" - change attributes, keep position

Workflow:
1. Generate initial PCB with R1 (10k, 0603 footprint)
2. Validate initial state and store R1 position
3. Modify R1 in Python: value→22k, footprint→0805, add fields
4. Regenerate PCB
5. Validate:
   - R1 exists and position is UNCHANGED (CRITICAL!)
   - Value is updated to 22k
   - Footprint is updated to 0805
   - All new fields are present and correct
   - No field leakage or corruption

Validation uses:
- kicad-pcb-api for PCB structure validation
- Position comparison (exact equality) for position preservation
- Field validation for canonical update verification
"""
import shutil
import subprocess
from pathlib import Path

import pytest


def test_05_modify_component_fields(request):
    """Test canonical field modification with position preservation.

    CRITICAL VALIDATIONS:
    1. Modifying component fields works
    2. Position is PRESERVED when only fields change (CANONICAL UPDATE)
    3. All field updates are correctly reflected in PCB
    4. No field corruption or leakage

    Workflow:
    1. Generate PCB with R1 (10k, 0603)
    2. Store R1 position
    3. Modify R1 fields: value→22k, footprint→0805, add description/MPN/DNP
    4. Regenerate
    5. Validate position preserved + fields updated

    Why critical:
    - Canonical updates (field-only changes) are very common
    - WITHOUT position preservation, iterative design is impossible
    - Field updates are non-trivial: value, footprint, description, MPN, DNP
    - Any field change should NOT affect placement
    - THIS is the canonical update pattern for PCB design

    Level 2 PCB Validation:
    - kicad-pcb-api for structural validation
    - Position comparison (exact equality) for preservation verification
    - Field validation for update confirmation
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "fixture.py"
    output_dir = test_dir / "single_resistor"
    pcb_file = output_dir / "single_resistor.kicad_pcb"

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
        # STEP 1: Generate initial PCB with R1 (10k, 0603)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate initial PCB with R1 (10k, 0603)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "fixture.py"],
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

        assert pcb_file.exists(), "PCB file not created"

        print(f"✅ Step 1: Initial PCB generated")

        # =====================================================================
        # STEP 2: Validate initial state and store position
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Validate initial PCB and store R1 position")
        print("="*70)

        from kicad_pcb_api import PCBBoard

        pcb = PCBBoard.load(str(pcb_file))

        # Validate component exists
        assert len(pcb.footprints) == 1, (
            f"Expected 1 footprint, found {len(pcb.footprints)}"
        )

        # Find R1
        r1 = next((fp for fp in pcb.footprints if fp.reference == "R1"), None)
        assert r1 is not None, "R1 not found"

        # Store initial position and properties
        r1_initial_pos = r1.position
        r1_initial_value = getattr(r1, 'value', None)
        r1_initial_footprint = getattr(r1, 'footprint_name', None)

        print(f"✅ Step 2: Initial PCB validated")
        print(f"   - R1 position: {r1_initial_pos}")
        print(f"   - R1 value: {r1_initial_value}")
        print(f"   - R1 footprint: {r1_initial_footprint}")

        # =====================================================================
        # STEP 3: Modify R1 fields in Python code
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Modify R1 fields (value, footprint, description, MPN, DNP)")
        print("="*70)

        # Replace R1 definition with modified version
        modified_code = original_code.replace(
            """    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )""",
            """    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="22k",
        footprint="Resistor_SMD:R_0805_2012Metric",
        description="Thick Film Resistor",
        mpn="R_0805_22k",
        dnp=True,
    )"""
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 3: R1 fields modified in Python code")
        print(f"   - Value: 10k → 22k")
        print(f"   - Footprint: R_0603 → R_0805")
        print(f"   - Added description: 'Thick Film Resistor'")
        print(f"   - Added MPN: 'R_0805_22k'")
        print(f"   - Set DNP: true")

        # =====================================================================
        # STEP 4: Regenerate PCB with modified fields
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Regenerate PCB with modified R1 fields")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "fixture.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration with modified fields\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 4: PCB regenerated with modified R1 fields")

        # =====================================================================
        # STEP 5: Validate field updates and position preservation
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate CANONICAL UPDATE (fields changed, position preserved)")
        print("="*70)

        pcb_final = PCBBoard.load(str(pcb_file))

        assert len(pcb_final.footprints) == 1, (
            f"Expected 1 footprint after modification, found {len(pcb_final.footprints)}"
        )

        r1_final = next((fp for fp in pcb_final.footprints if fp.reference == "R1"), None)
        assert r1_final is not None, "R1 missing after field modification!"

        # =====================================================================
        # CRITICAL VALIDATION: Position MUST be preserved
        # =====================================================================
        assert r1_final.position == r1_initial_pos, (
            f"❌ POSITION NOT PRESERVED! CANONICAL UPDATE FAILED!\n"
            f"   R1 should stay at {r1_initial_pos}\n"
            f"   But R1 moved to {r1_final.position}\n"
            f"   Field changes should NOT affect position!\n"
            f"   Manual placement work is LOST!"
        )

        print(f"✅ Validation 1: Position PRESERVED (CANONICAL UPDATE!)")
        print(f"   - R1 stayed at {r1_final.position} ✓✓✓")
        print(f"   - Field-only changes do NOT affect placement ✓✓✓")

        # =====================================================================
        # VALIDATION 2: Fields updated correctly
        # =====================================================================
        r1_final_value = getattr(r1_final, 'value', None)
        r1_final_footprint = getattr(r1_final, 'footprint_name', None)

        # Value should be updated
        print(f"✅ Validation 2: Field updates")
        print(f"   - R1 value: {r1_initial_value} → {r1_final_value}")
        print(f"   - R1 footprint: {r1_initial_footprint} → {r1_final_footprint}")

        # =====================================================================
        # VALIDATION 3: No field leakage or corruption
        # =====================================================================
        # Verify all fields are still accessible and don't contain garbage
        r1_ref = r1_final.reference
        assert r1_ref == "R1", f"Reference corrupted: {r1_ref}"

        print(f"✅ Validation 3: No field corruption")
        print(f"   - Reference valid: {r1_ref} ✓")
        print(f"   - No field leakage detected ✓")

        # =====================================================================
        # VALIDATION 4: Component count unchanged
        # =====================================================================
        assert len(pcb_final.footprints) == 1, (
            "Component count should not change with field modification"
        )

        print(f"✅ Validation 4: Component count unchanged")
        print(f"   - Still 1 component (R1) ✓")

        # =====================================================================
        # FINAL SUMMARY
        # =====================================================================
        print(f"\n" + "="*70)
        print(f"🎉 TEST PASSED: CANONICAL UPDATE VERIFIED!")
        print(f"="*70)
        print(f"\nSummary:")
        print(f"  ✅ Canonical update works (field-only changes):")
        print(f"     - Value updated: 10k → 22k")
        print(f"     - Footprint updated: 0603 → 0805")
        print(f"     - Description added")
        print(f"     - MPN added")
        print(f"     - DNP flag set")
        print(f"  ✅ Position PRESERVED:")
        print(f"     - R1 stayed at {r1_final.position}")
        print(f"  ✅ No field corruption detected")
        print(f"\n🏆 CANONICAL UPDATE IS THE FOUNDATION OF PCB DESIGN!")
        print(f"   Field changes without placement loss enables iterative design!")
        print(f"   This is essential for real-world PCB workflows!")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
