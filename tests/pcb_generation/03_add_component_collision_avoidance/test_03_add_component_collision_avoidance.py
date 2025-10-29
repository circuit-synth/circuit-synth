#!/usr/bin/env python3
"""
Automated test for 03_add_component_collision_avoidance PCB test.

Tests adding components with smart auto-placement and collision avoidance.

This validates that you can:
1. Generate PCB with initial 2 resistors (R1, R2)
2. Add R3 in Python
3. Regenerate PCB
4. CRITICAL: R1 and R2 positions preserved
5. R3 is auto-placed WITHOUT overlapping existing components
6. R3 is NOT placed at origin (0, 0) - smart placement works
7. No collision/overlap detected between any components

This is critical because:
- Adding components is common (decoupling caps, test points, debug headers)
- Placement preservation proves existing work is safe (Test 02)
- Smart auto-placement proves circuit-synth handles new components intelligently
- Collision avoidance ensures auto-placement is reliable
- Together, this enables iterative PCB development

Workflow:
1. Generate initial PCB with R1, R2
2. Validate initial state
3. Store R1, R2 positions
4. Add R3 in Python
5. Regenerate PCB
6. Validate:
   - R1, R2 positions preserved (placement preservation)
   - R3 exists and was auto-placed
   - R3 not at origin (0, 0) - intelligent placement
   - All components spaced with minimum distance (no collisions)
   - All components within board boundaries

Validation uses:
- kicad-pcb-api for PCB structure validation
- Position comparison for preservation
- Collision detection (minimum spacing validation)
- Bounds checking (components within board)
"""
import shutil
import subprocess
from pathlib import Path

import pytest


def test_03_add_component_collision_avoidance(request):
    """Test adding component with smart auto-placement and collision avoidance.

    CRITICAL VALIDATIONS:
    1. Adding components works
    2. Existing placements preserved (placement preservation)
    3. Auto-placement doesn't overlap existing components (collision avoidance)
    4. Auto-placement is intelligent (not at origin)

    Workflow:
    1. Generate PCB with R1, R2
    2. Add R3 in Python
    3. Regenerate
    4. Validate R1, R2 preserved + R3 auto-placed without collisions

    Why critical:
    - Common workflow: add decoupling caps, test points, debug headers
    - Without collision avoidance, auto-placement is unreliable
    - Proves placement preservation works for additions (not just changes)
    - Proves auto-placement algorithm is intelligent

    Level 2 PCB Validation:
    - kicad-pcb-api for structural validation
    - Position comparison for preservation
    - Collision detection for auto-placement reliability
    - Bounds checking for component placement validity
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "fixture.py"
    output_dir = test_dir / "add_component_test"
    pcb_file = output_dir / "add_component_test.kicad_pcb"

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

        from kicad_pcb_api import PCBBoard

        pcb = PCBBoard.load(str(pcb_file))

        # Validate components exist
        assert len(pcb.footprints) == 2, (
            f"Expected 2 footprints, found {len(pcb.footprints)}"
        )

        # Find and store initial positions
        r1 = next((fp for fp in pcb.footprints if fp.reference == "R1"), None)
        r2 = next((fp for fp in pcb.footprints if fp.reference == "R2"), None)

        assert r1 is not None, "R1 not found"
        assert r2 is not None, "R2 not found"

        r1_initial_pos = r1.position
        r2_initial_pos = r2.position

        print(f"✅ Step 2: Initial PCB validated")
        print(f"   - R1 position: {r1_initial_pos}")
        print(f"   - R2 position: {r2_initial_pos}")

        # =====================================================================
        # STEP 3: Add R3 in Python code
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Add R3 to Python code")
        print("="*70)

        # Add R3 (replace placeholder with actual component)
        modified_code = original_code.replace(
            "    # ADD R3 HERE",
            """    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="47k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )"""
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 3: R3 added to Python code")

        # =====================================================================
        # STEP 4: Regenerate PCB
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Regenerate PCB with R3")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "fixture.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration with R3\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 4: PCB regenerated with R3")

        # =====================================================================
        # STEP 5: Validate placement preservation and auto-placement
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate preservation and auto-placement")
        print("="*70)

        pcb_final = PCBBoard.load(str(pcb_file))

        assert len(pcb_final.footprints) == 3, (
            f"Expected 3 footprints after addition, found {len(pcb_final.footprints)}"
        )

        r1_final = next((fp for fp in pcb_final.footprints if fp.reference == "R1"), None)
        r2_final = next((fp for fp in pcb_final.footprints if fp.reference == "R2"), None)
        r3_final = next((fp for fp in pcb_final.footprints if fp.reference == "R3"), None)

        assert r1_final is not None, "R1 missing after regeneration!"
        assert r2_final is not None, "R2 missing after regeneration!"
        assert r3_final is not None, "R3 missing after regeneration!"

        # =====================================================================
        # VALIDATION 1: Placement preservation (Test 02 foundation)
        # =====================================================================
        assert r1_final.position == r1_initial_pos, (
            f"R1 position not preserved!\n"
            f"   Before: {r1_initial_pos}\n"
            f"   After: {r1_final.position}"
        )

        assert r2_final.position == r2_initial_pos, (
            f"R2 position not preserved!\n"
            f"   Before: {r2_initial_pos}\n"
            f"   After: {r2_final.position}"
        )

        print(f"✅ Validation 1: Placement PRESERVED")
        print(f"   - R1 at {r1_final.position} ✓")
        print(f"   - R2 at {r2_final.position} ✓")

        # =====================================================================
        # VALIDATION 2: R3 auto-placement is intelligent
        # =====================================================================
        assert r3_final.position != (0.0, 0.0), (
            "R3 appears to be unplaced (at origin 0,0) - auto-placement failed!"
        )

        print(f"✅ Validation 2: R3 intelligent auto-placement")
        print(f"   - R3 NOT at origin ✓")
        print(f"   - R3 auto-placed at {r3_final.position} ✓")

        # =====================================================================
        # VALIDATION 3: Collision avoidance
        # =====================================================================
        def check_no_collision(fp1, fp2, min_distance_mm=5.0):
            """Check that two footprints are spaced apart."""
            x1, y1 = fp1.position
            x2, y2 = fp2.position
            distance = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
            return distance >= min_distance_mm

        assert check_no_collision(r1_final, r2_final), (
            f"R1 and R2 overlapping!\n"
            f"   R1 at {r1_final.position}, R2 at {r2_final.position}"
        )

        assert check_no_collision(r1_final, r3_final), (
            f"R3 at {r3_final.position} overlaps with R1 at {r1_final.position}"
        )

        assert check_no_collision(r2_final, r3_final), (
            f"R3 at {r3_final.position} overlaps with R2 at {r2_final.position}"
        )

        print(f"✅ Validation 3: Collision avoidance")
        print(f"   - R1 ↔ R2: distance OK ✓")
        print(f"   - R1 ↔ R3: distance OK ✓")
        print(f"   - R2 ↔ R3: distance OK ✓")

        # =====================================================================
        # VALIDATION 4: Components within reasonable board bounds
        # =====================================================================
        max_x = max([fp.position[0] for fp in pcb_final.footprints])
        max_y = max([fp.position[1] for fp in pcb_final.footprints])

        # Components should be within a reasonable area (not infinitely far)
        assert max_x < 500.0 and max_y < 500.0, (
            f"Components placed too far apart (max: {max_x}, {max_y})"
        )

        print(f"✅ Validation 4: Component bounds")
        print(f"   - Max X: {max_x:.1f}mm ✓")
        print(f"   - Max Y: {max_y:.1f}mm ✓")

        # =====================================================================
        # FINAL SUMMARY
        # =====================================================================
        print(f"\n" + "="*70)
        print(f"✅ TEST PASSED: Add Component with Collision Avoidance")
        print(f"="*70)
        print(f"\nSummary:")
        print(f"  ✅ Placement preserved:")
        print(f"     - R1 stayed at {r1_final.position}")
        print(f"     - R2 stayed at {r2_final.position}")
        print(f"  ✅ Component addition works:")
        print(f"     - R3 added and auto-placed")
        print(f"  ✅ Smart auto-placement:")
        print(f"     - R3 NOT at origin (intelligent)")
        print(f"     - R3 at {r3_final.position}")
        print(f"  ✅ Collision avoidance:")
        print(f"     - All components properly spaced")
        print(f"     - Minimum 5mm separation maintained")
        print(f"\n🏆 Adding components to PCB works reliably!")
        print(f"   Iterative development with component additions is viable!")

    finally:
        # Restore original Python file (R3 removed)
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
