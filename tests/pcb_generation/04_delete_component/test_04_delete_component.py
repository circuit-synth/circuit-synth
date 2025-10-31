#!/usr/bin/env python3
"""
Automated test for 04_delete_component PCB test.

Tests that removing a component from Python code correctly regenerates the PCB.

This validates that you can:
1. Generate PCB with 3 resistors (R1, R2, R3)
2. Validate all 3 components exist and store their positions
3. Remove R2 from Python code
4. Regenerate PCB
5. CRITICAL: R1 and R3 still exist with positions preserved
6. R2 is gone from the PCB

This is critical because:
- Iterative PCB design often involves removing components
- Without proper deletion handling, removing components could break the design
- Placement preservation means manual work on R1 and R3 is NOT lost
- Validates that deletion workflow is reliable and safe

Workflow:
1. Generate initial PCB with R1, R2, R3
2. Validate all 3 components exist and store positions
3. Remove R2 from Python code
4. Regenerate PCB
5. Validate:
   - R1 exists at original position (placement preserved)
   - R3 exists at original position (placement preserved)
   - R2 is gone (deletion worked)

Validation uses:
- kicad-pcb-api for PCB structure validation
- Position comparison for preservation verification
- Component count validation for deletion confirmation
"""
import shutil
import subprocess
from pathlib import Path

import pytest


def test_04_delete_component(request):
    """Test component deletion with placement preservation.

    CRITICAL VALIDATIONS:
    1. Deleting components works
    2. Remaining components stay at their original positions
    3. Deleted component is completely removed

    Workflow:
    1. Generate PCB with R1, R2, R3
    2. Remove R2 from Python
    3. Regenerate
    4. Validate R1, R3 preserved + R2 deleted

    Why critical:
    - Common workflow: remove unnecessary components, add test points
    - Without preservation, deleting a component loses work on others
    - Validates deletion doesn't corrupt remaining placements
    - Proves design is safe for iterative component management

    Level 2 PCB Validation:
    - kicad-pcb-api for structural validation
    - Position comparison for preservation verification
    - Component count validation for deletion confirmation
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "fixture.py"
    output_dir = test_dir / "three_resistors"
    pcb_file = output_dir / "three_resistors.kicad_pcb"

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
        # STEP 1: Generate initial PCB with R1, R2, R3
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate initial PCB with R1, R2, R3")
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
        # STEP 2: Validate initial state and store positions
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Validate initial PCB structure (R1, R2, R3)")
        print("="*70)

        from kicad_pcb_api import PCBBoard

        pcb = PCBBoard(str(pcb_file))

        # Validate components exist
        assert len(pcb.footprints) == 3, (
            f"Expected 3 footprints, found {len(pcb.footprints)}"
        )

        # Find components and store positions
        r1 = next((fp for fp in pcb.footprints if fp.reference == "R1"), None)
        r2 = next((fp for fp in pcb.footprints if fp.reference == "R2"), None)
        r3 = next((fp for fp in pcb.footprints if fp.reference == "R3"), None)

        assert r1 is not None, "R1 not found"
        assert r2 is not None, "R2 not found"
        assert r3 is not None, "R3 not found"

        r1_initial_pos = r1.position
        r2_initial_pos = r2.position
        r3_initial_pos = r3.position

        print(f"✅ Step 2: Initial PCB validated")
        print(f"   - R1 initial position: {r1_initial_pos}")
        print(f"   - R2 initial position: {r2_initial_pos}")
        print(f"   - R3 initial position: {r3_initial_pos}")

        # =====================================================================
        # STEP 3: Remove R2 from Python code
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Remove R2 from Python code")
        print("="*70)

        # Remove R2 component definition
        modified_code = original_code.replace(
            """    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="22k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
""",
            ""
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 3: R2 removed from Python code")

        # =====================================================================
        # STEP 4: Regenerate PCB without R2
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Regenerate PCB without R2")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "fixture.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration without R2\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 4: PCB regenerated without R2")

        # =====================================================================
        # STEP 5: Validate deletion and placement preservation
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate deletion and placement preservation")
        print("="*70)

        pcb_final = PCBBoard(str(pcb_file))

        # Should now have only 2 components (R1 and R3)
        assert len(pcb_final.footprints) == 2, (
            f"Expected 2 footprints after deletion, found {len(pcb_final.footprints)}. "
            f"References: {[fp.reference for fp in pcb_final.footprints]}"
        )

        r1_final = next((fp for fp in pcb_final.footprints if fp.reference == "R1"), None)
        r3_final = next((fp for fp in pcb_final.footprints if fp.reference == "R3"), None)
        r2_final = next((fp for fp in pcb_final.footprints if fp.reference == "R2"), None)

        # =====================================================================
        # VALIDATION 1: R2 is deleted
        # =====================================================================
        assert r2_final is None, (
            f"❌ R2 NOT DELETED! R2 still exists in PCB!\n"
            f"   This indicates component deletion failed.\n"
            f"   Components in PCB: {[fp.reference for fp in pcb_final.footprints]}"
        )

        print(f"✅ Validation 1: R2 successfully deleted")
        print(f"   - R2 is gone from PCB ✓")

        # =====================================================================
        # VALIDATION 2: R1 position preserved
        # =====================================================================
        assert r1_final is not None, "R1 missing after deletion!"

        assert r1_final.position == r1_initial_pos, (
            f"❌ R1 POSITION NOT PRESERVED! Placement work LOST!\n"
            f"   Before: {r1_initial_pos}\n"
            f"   After: {r1_final.position}\n"
            f"   Deletion should not move remaining components!"
        )

        print(f"✅ Validation 2: R1 position PRESERVED")
        print(f"   - R1 stayed at {r1_final.position} ✓")

        # =====================================================================
        # VALIDATION 3: R3 position preserved
        # =====================================================================
        assert r3_final is not None, "R3 missing after deletion!"

        assert r3_final.position == r3_initial_pos, (
            f"❌ R3 POSITION NOT PRESERVED! Placement work LOST!\n"
            f"   Before: {r3_initial_pos}\n"
            f"   After: {r3_final.position}\n"
            f"   Deletion should not move remaining components!"
        )

        print(f"✅ Validation 3: R3 position PRESERVED")
        print(f"   - R3 stayed at {r3_final.position} ✓")

        # =====================================================================
        # FINAL SUMMARY
        # =====================================================================
        print(f"\n" + "="*70)
        print(f"✅ TEST PASSED: Component Deletion with Placement Preservation")
        print(f"="*70)
        print(f"\nSummary:")
        print(f"  ✅ Component deletion works:")
        print(f"     - R2 successfully removed from PCB")
        print(f"  ✅ Remaining components preserved:")
        print(f"     - R1 stayed at {r1_final.position}")
        print(f"     - R3 stayed at {r3_final.position}")
        print(f"  ✅ No placement corruption from deletion")
        print(f"\n🏆 Component deletion is safe and reliable!")
        print(f"   Iterative design with component removal is viable!")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
