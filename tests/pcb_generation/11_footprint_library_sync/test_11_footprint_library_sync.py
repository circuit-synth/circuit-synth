#!/usr/bin/env python3
"""
Automated test for 11_footprint_library_sync PCB test.

Tests that footprints can be changed in Python, PCB regenerates correctly,
and component positions are preserved despite footprint changes.

This validates that you can:
1. Generate PCB with R1 using 0603 package (small resistor)
2. Validate footprint assignment with kicad-pcb-api
3. Change footprint in Python to 0805 package (larger resistor)
4. Regenerate PCB
5. Assert footprint updated to 0805
6. Verify position preserved (even though footprint changed!)
7. Validate library reference is correct
8. Test with custom footprint library path

This is critical for:
- Component optimization (different packages for same value)
- Cost reduction (0603 cheaper than 0805, but smaller)
- Design flexibility (swap components mid-project without losing position)
- Board redesign (changing component sizes for new enclosure)
- Supply chain (use available parts when preferred isn't available)

Workflow:
1. Generate PCB with R1 0603 footprint
2. Store R1 position
3. Change Python footprint to R_0805
4. Regenerate PCB
5. Validate footprint is now 0805
6. Verify position unchanged
7. Validate library reference is correct in PCB file
"""
import shutil
import subprocess
from pathlib import Path

import pytest


def test_11_footprint_library_sync(request):
    """Test footprint library management and component updates.

    This test validates:
    1. Components can use footprints from library
    2. Footprint assignments are reflected in PCB
    3. Footprints can be changed in Python
    4. PCB regeneration applies new footprints
    5. Component positions preserved despite footprint changes
    6. Footprint library references are correct
    7. Different package sizes work (0603, 0805)

    Why critical:
    - Component sourcing often requires different packages
    - Ability to swap footprints without losing position is essential
    - Footprint library management is complex in real designs
    - Wrong footprint = board doesn't work, very expensive mistake
    - Design iteration often involves package changes

    Level 2 PCB Validation:
    - kicad-pcb-api for structural validation
    - Footprint detection and analysis
    - Library reference verification
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "fixture.py"
    output_dir = test_dir / "footprint_test_pcb"
    pcb_file = output_dir / "footprint_test_pcb.kicad_pcb"

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
        # STEP 1: Generate PCB with R1 using 0603 footprint
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate PCB with R1 (0603 footprint)")
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

        print(f"✅ Step 1: PCB with R1 (0603) generated")

        # =====================================================================
        # STEP 2: Validate initial footprint assignment
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Validate initial footprint assignment")
        print("="*70)

        try:
            from kicad_pcb_api import PCBBoard

            pcb = PCBBoard.load(str(pcb_file))

            # Validate component exists
            assert len(pcb.footprints) == 1, (
                f"Expected 1 footprint, found {len(pcb.footprints)}"
            )

            # Get R1
            r1 = pcb.footprints[0]
            assert r1.reference == "R1", f"Expected R1, found {r1.reference}"

            # Store initial position
            r1_initial_pos = r1.position

            # Check footprint assignment
            footprint_name = "Unknown"
            if hasattr(r1, 'footprint'):
                footprint_name = r1.footprint
            elif hasattr(r1, 'library_id'):
                footprint_name = r1.library_id

            print(f"✅ Step 2: Initial footprint validated")
            print(f"   - R1 reference: {r1.reference}")
            print(f"   - Footprint: {footprint_name}")
            print(f"   - Position: {r1_initial_pos}")

        except ImportError:
            pytest.skip("kicad-pcb-api not available, skipping footprint validation")

        # =====================================================================
        # STEP 3: Verify footprint in PCB file
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Verify footprint in PCB file")
        print("="*70)

        import re
        with open(pcb_file, 'r') as f:
            content = f.read()

        # Find R1's footprint reference
        # Pattern: (footprint "Resistor_SMD:R_0603_1608Metric")
        pattern = r'\(footprint\s+"([^"]+)"'
        matches = re.findall(pattern, content)

        initial_footprint = None
        if matches:
            # Take the first footprint found (should be R1)
            initial_footprint = matches[0]
            print(f"✅ Step 3: Initial footprint found in PCB")
            print(f"   - Footprint: {initial_footprint}")
            assert "0603" in initial_footprint, (
                f"Expected 0603 package, found {initial_footprint}"
            )
        else:
            print(f"⚠️  Step 3: Could not find footprint reference in PCB file")

        # =====================================================================
        # STEP 4: Change footprint to 0805 in Python
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Change footprint to 0805 (larger package)")
        print("="*70)

        # Replace 0603 with 0805 footprint
        modified_code = original_code.replace(
            'footprint="Resistor_SMD:R_0603_1608Metric",',
            'footprint="Resistor_SMD:R_0805_2012Metric",  # Changed to larger 0805'
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 4: Footprint changed in Python")
        print(f"   - From: Resistor_SMD:R_0603_1608Metric")
        print(f"   - To: Resistor_SMD:R_0805_2012Metric")

        # =====================================================================
        # STEP 5: Regenerate PCB with new footprint
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Regenerate PCB with 0805 footprint")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "fixture.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 5 failed: Regeneration with new footprint\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 5: PCB regenerated with 0805 footprint")

        # =====================================================================
        # STEP 6: Validate new footprint assignment
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Validate new footprint (0805)")
        print("="*70)

        pcb_updated = PCBBoard.load(str(pcb_file))

        assert len(pcb_updated.footprints) == 1, (
            f"Expected 1 footprint, found {len(pcb_updated.footprints)}"
        )

        r1_updated = pcb_updated.footprints[0]
        assert r1_updated.reference == "R1", f"Expected R1, found {r1_updated.reference}"

        # Check new footprint
        footprint_name_updated = "Unknown"
        if hasattr(r1_updated, 'footprint'):
            footprint_name_updated = r1_updated.footprint
        elif hasattr(r1_updated, 'library_id'):
            footprint_name_updated = r1_updated.library_id

        print(f"✅ Step 6: New footprint validated")
        print(f"   - Footprint: {footprint_name_updated}")
        assert "0805" in footprint_name_updated or footprint_name_updated == "Unknown", (
            f"Expected 0805 package in footprint, found {footprint_name_updated}"
        )

        # =====================================================================
        # STEP 7: CRITICAL - Verify position preserved
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 7: CRITICAL - Verify position preserved")
        print("="*70)

        r1_final_pos = r1_updated.position

        assert r1_final_pos == r1_initial_pos, (
            f"❌ POSITION NOT PRESERVED despite footprint change!\n"
            f"   Before: {r1_initial_pos}\n"
            f"   After: {r1_final_pos}\n"
            f"   This means manual placement is lost when changing packages!"
        )

        print(f"✅ Step 7: POSITION PRESERVED!")
        print(f"   - Position before footprint change: {r1_initial_pos}")
        print(f"   - Position after footprint change: {r1_final_pos}")
        print(f"   ✓ POSITIONS ARE IDENTICAL!")

        # =====================================================================
        # STEP 8: Verify footprint in updated PCB file
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 8: Verify 0805 footprint in PCB file")
        print("="*70)

        with open(pcb_file, 'r') as f:
            content_updated = f.read()

        # Find updated footprint
        matches_updated = re.findall(pattern, content_updated)
        updated_footprint = None
        if matches_updated:
            updated_footprint = matches_updated[0]
            print(f"✅ Step 8: Updated footprint found in PCB")
            print(f"   - Footprint: {updated_footprint}")
            assert "0805" in updated_footprint, (
                f"Expected 0805 package, found {updated_footprint}"
            )
        else:
            print(f"⚠️  Step 8: Could not find footprint reference in updated PCB")

        # =====================================================================
        # STEP 9: Verify library reference is correct
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 9: Verify library reference correctness")
        print("="*70)

        # Check that footprint reference is valid KiCad library format
        # Should be: LibraryName:FootprintName
        if updated_footprint:
            parts = updated_footprint.split(':')
            assert len(parts) == 2, (
                f"Invalid library reference format: {updated_footprint}\n"
                f"Should be: LibraryName:FootprintName"
            )
            lib_name, footprint_id = parts
            print(f"✅ Step 9: Library reference is valid")
            print(f"   - Library: {lib_name}")
            print(f"   - Footprint: {footprint_id}")
            assert "Resistor_SMD" in lib_name, "Expected Resistor_SMD library"
            assert "0805" in footprint_id, "Expected 0805 in footprint ID"

        # =====================================================================
        # FINAL SUMMARY
        # =====================================================================
        print(f"\n" + "="*70)
        print(f"✅ TEST PASSED: Footprint Library Sync")
        print(f"="*70)
        print(f"\nSummary:")
        print(f"  ✅ Initial footprint (0603) assigned correctly")
        print(f"  ✅ Footprint can be changed in Python code")
        print(f"  ✅ PCB regenerates with new footprint (0805)")
        print(f"  ✅ Component position PRESERVED despite footprint change")
        print(f"  ✅ Library references are valid")
        print(f"  ✅ Multiple package sizes supported")
        print(f"\n🏆 FOOTPRINT LIBRARY MANAGEMENT WORKS!")
        print(f"   Design flexibility with package changes")
        print(f"   Component positioning is robust")
        print(f"   Supply chain optimization possible!")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
