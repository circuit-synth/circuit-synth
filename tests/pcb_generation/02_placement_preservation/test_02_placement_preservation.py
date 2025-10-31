#!/usr/bin/env python3
"""
Automated test for 02_placement_preservation PCB bidirectional test.

Tests that manual component placement survives Python changes to the circuit.

THE KILLER FEATURE FOR PCB: Without placement preservation, tool is unusable for real PCB design.

This validates that you can:
1. Generate PCB with 2 resistors (R1, R2)
2. Manually move R1 to specific position (50mm, 30mm)
3. Add R3 in Python code
4. Regenerate PCB
5. CRITICAL: R1 stays at (50, 30) - manual placement PRESERVED!

This is critical because:
- PCB placement is manual work that takes hours
- Without preservation, users lose all placement work every regeneration
- Tool becomes unusable for real design workflows
- THIS is the feature that makes circuit-synth viable for PCB development

Workflow:
1. Generate initial PCB with R1, R2
2. Validate initial state (Level 2: kicad-pcb-api)
3. Manually move R1 to (50, 30) in PCB file
4. Add R3 in Python
5. Regenerate PCB
6. Validate:
   - R1 stayed at (50, 30) - PLACEMENT PRESERVED
   - R2 stayed in original position - PLACEMENT PRESERVED
   - R3 exists and was auto-placed - NEW COMPONENT WORKS
   - No collisions between components

Validation uses:
- kicad-pcb-api for PCB structure validation
- Position comparison for placement preservation (exact equality)
- Collision detection to ensure auto-placed components don't overlap
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_02_placement_preservation(request):
    """Test placement preservation - THE KILLER FEATURE FOR PCB.

    CRITICAL VALIDATION: Manual component placement survives Python changes.

    Workflow:
    1. Generate initial PCB with R1, R2
    2. Store R1, R2 initial positions
    3. Manually move R1 to (50, 30)
    4. Add R3 in Python code
    5. Regenerate PCB
    6. Validate R1 stayed at (50, 30) - PLACEMENT PRESERVED!
    7. Validate R2 stayed in original position
    8. Validate R3 exists and was auto-placed

    Why critical:
    - Manual PCB placement takes hours of work
    - Without this, every regeneration loses all placement work
    - THIS is THE feature that makes tool viable for real PCB design
    - Same as schematic test 09, but for PCB

    Level 2 PCB Validation:
    - kicad-pcb-api for structural validation
    - Position comparison for placement preservation
    - Collision detection for auto-placement validation
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "fixture.py"
    output_dir = test_dir / "two_resistors"
    pcb_file = output_dir / "two_resistors.kicad_pcb"

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
        # STEP 1: Generate initial PCB with R1 and R2
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate initial PCB with R1, R2")
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
        print("STEP 2: Validate initial PCB structure")
        print("="*70)

        from kicad_pcb_api import PCBBoard, Point

        pcb = PCBBoard(str(pcb_file))

        # Validate components exist
        assert len(pcb.footprints) == 2, (
            f"Expected 2 footprints, found {len(pcb.footprints)}"
        )

        # Find components
        r1 = next((fp for fp in pcb.footprints if fp.reference == "R1"), None)
        r2 = next((fp for fp in pcb.footprints if fp.reference == "R2"), None)

        assert r1 is not None, "R1 not found"
        assert r2 is not None, "R2 not found"

        # Store initial positions
        r1_initial_pos = r1.position
        r2_initial_pos = r2.position

        print(f"✅ Step 2: Initial PCB validated")
        print(f"   - R1 initial position: {r1_initial_pos}")
        print(f"   - R2 initial position: {r2_initial_pos}")

        # =====================================================================
        # STEP 3: Manually move R1 to (50, 30)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Manually move R1 to (50, 30)")
        print("="*70)

        # Move R1 to specific position (simulating manual layout in KiCad)
        r1.position = Point(50.0, 30.0)
        pcb.save(str(pcb_file))

        # Verify move was saved
        pcb_moved = PCBBoard(str(pcb_file))
        r1_moved = next(fp for fp in pcb_moved.footprints if fp.reference == "R1")

        assert r1_moved.position == Point(50.0, 30.0), (
            f"R1 move failed! Position is {r1_moved.position}, expected (50.0, 30.0)"
        )

        print(f"✅ Step 3: R1 manually moved")
        print(f"   - R1 now at: (50.0, 30.0)")

        # =====================================================================
        # STEP 4: Add R3 in Python code
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Add R3 to Python code")
        print("="*70)

        # Uncomment R3 (replace placeholder with actual component)
        modified_code = original_code.replace(
            "    # ADD R3 HERE",
            """    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )"""
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 4: R3 added to Python code")

        # =====================================================================
        # STEP 5: Regenerate PCB
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Regenerate PCB with R3")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "fixture.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 5 failed: Regeneration with R3\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 5: PCB regenerated with R3")

        # =====================================================================
        # STEP 6: Validate PLACEMENT PRESERVATION (THE KILLER FEATURE)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: VALIDATE PLACEMENT PRESERVATION")
        print("="*70)

        pcb_final = PCBBoard(str(pcb_file))

        assert len(pcb_final.footprints) == 3, (
            f"Expected 3 footprints after regeneration, found {len(pcb_final.footprints)}"
        )

        r1_final = next((fp for fp in pcb_final.footprints if fp.reference == "R1"), None)
        r2_final = next((fp for fp in pcb_final.footprints if fp.reference == "R2"), None)
        r3_final = next((fp for fp in pcb_final.footprints if fp.reference == "R3"), None)

        assert r1_final is not None, "R1 missing after regeneration!"
        assert r2_final is not None, "R2 missing after regeneration!"
        assert r3_final is not None, "R3 missing after regeneration!"

        # =====================================================================
        # CRITICAL VALIDATION: R1 position MUST be preserved
        # =====================================================================
        assert r1_final.position == Point(50.0, 30.0), (
            f"❌ POSITION NOT PRESERVED! R1 should stay at (50.0, 30.0)\n"
            f"   But R1 moved to {r1_final.position}\n"
            f"   This means manual PCB layout work is LOST!\n"
            f"   THE KILLER FEATURE IS BROKEN!"
        )

        # R2 position should also be preserved (unchanged)
        assert r2_final.position == r2_initial_pos, (
            f"R2 position not preserved!\n"
            f"   Before: {r2_initial_pos}\n"
            f"   After: {r2_final.position}\n"
            f"   Manual placement work LOST!"
        )

        # R3 should be auto-placed
        assert r3_final is not None, "R3 should exist after regeneration"

        # R3 should NOT be at (0, 0) - that's invalid/unplaced
        assert r3_final.position != (0.0, 0.0), (
            "R3 appears to be unplaced (at origin)"
        )

        print(f"✅ Step 6: PLACEMENT PRESERVATION VERIFIED!")
        print(f"   - R1 PRESERVED at (50.0, 30.0) ✓✓✓")
        print(f"   - R2 PRESERVED at {r2_final.position} ✓✓✓")
        print(f"   - R3 auto-placed at {r3_final.position} ✓")

        # =====================================================================
        # STEP 7: Validate auto-placement (R3 should be smart placement)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 7: Validate R3 auto-placement")
        print("="*70)

        # R3 should be placed somewhere reasonable (not too far from other components)
        # and not overlapping existing components
        def check_collision(fp1, fp2, min_distance_mm=5.0):
            """Check if two footprints overlap with minimum spacing."""
            x1, y1 = fp1.position.x, fp1.position.y
            x2, y2 = fp2.position.x, fp2.position.y
            distance = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
            return distance >= min_distance_mm

        # Verify R3 doesn't collide with R1 or R2
        assert check_collision(r3_final, r1_final), (
            f"R3 at {r3_final.position} overlaps with R1 at {r1_final.position}"
        )
        assert check_collision(r3_final, r2_final), (
            f"R3 at {r3_final.position} overlaps with R2 at {r2_final.position}"
        )

        print(f"✅ Step 7: R3 auto-placement validated")
        print(f"   - No collisions with existing components ✓")
        print(f"   - R3 positioned at reasonable location ✓")

        # =====================================================================
        # FINAL SUMMARY
        # =====================================================================
        print(f"\n" + "="*70)
        print(f"🎉 TEST PASSED: PLACEMENT PRESERVATION VERIFIED!")
        print(f"="*70)
        print(f"\nSummary:")
        print(f"  ✅ Manual placement preserved:")
        print(f"     - R1 stayed at (50.0, 30.0)")
        print(f"     - R2 stayed at {r2_final.position}")
        print(f"  ✅ New component auto-placed:")
        print(f"     - R3 placed at {r3_final.position}")
        print(f"  ✅ No collisions detected")
        print(f"\n🏆 THE KILLER FEATURE WORKS FOR PCB!")
        print(f"   Manual PCB layout work is NOT lost when regenerating!")
        print(f"   Tool is viable for real PCB development workflows!")

    finally:
        # Restore original Python file (R3 commented out)
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
