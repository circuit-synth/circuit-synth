#!/usr/bin/env python3
"""Test 11: sync_component_root_update_value - Update component value while preserving all others.

This test verifies that updating a component value (R1: 10k → 47k) preserves
ALL other schematic elements:
- Other components (R2, C1) remain completely unchanged
- Power symbols (VCC, GND) remain unchanged
- Labels (DATA, CLK) remain unchanged
- Modified component's other properties preserved (footprint, position, rotation)

Initial State:
- Components: R1(10k), R2(4.7k), C1(100nF)
- Power: VCC, GND
- Labels: DATA

Operation:
- Update R1 value: 10k → 47k

Expected Result:
- R1 value changed to 47k
- R1 footprint, position, rotation unchanged
- R2 and C1 completely unchanged
- Power and labels unchanged
- Sync log shows "🔄 Update: R1"
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_11_sync_component_root_update_value(request):
    """Test updating R1 value while preserving all other elements.

    Uses comprehensive_root fixture with ALL element types to ensure
    CRUD operation preserves everything except the modified value.
    """

    # Setup paths
    test_dir = Path(__file__).parent
    fixture_dir = test_dir.parent / "fixtures"
    python_file = fixture_dir / "comprehensive_root.py"
    output_dir = fixture_dir / "comprehensive_root"
    schematic_file = output_dir / "comprehensive_root.kicad_sch"

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
        # STEP 1: Generate with original values (R1=10k)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate comprehensive circuit with R1=10k")
        print("="*70)

        # Generate
        result = subprocess.run(
            ["uv", "run", "python", str(python_file)],
            cwd=fixture_dir,
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

        # COMPREHENSIVE VERIFICATION using helpers
        import sys
        sys.path.insert(0, str(test_dir.parent))
        from fixtures.helpers import (
            verify_components,
            verify_power_symbols,
            verify_labels,
            verify_component_properties
        )

        # Verify initial state
        components_before = verify_components(
            schematic_file,
            expected_refs={"R1", "R2", "C1"},
            message="Step 1: Components"
        )

        power_before = verify_power_symbols(
            schematic_file,
            expected_power={"VCC", "GND"},
            message="Step 1: Power"
        )

        labels_before = verify_labels(
            schematic_file,
            expected_labels={"DATA", "CLK"},
            message="Step 1: Labels"
        )

        # Verify R1 initial value
        verify_component_properties(
            components_before["R1"],
            expected_ref="R1",
            expected_value="10k",
            expected_footprint="0603",
            expected_symbol="Device:R",
            message="Step 1: R1 initial"
        )

        # Store initial state for comparison
        r1_before = components_before["R1"]
        r2_before = components_before["R2"]
        c1_before = components_before["C1"]

        print(f"✅ Step 1: Initial state verified")
        print(f"   Components: {sorted(components_before.keys())}")
        print(f"   R1: {r1_before.value} @ {r1_before.position}, {r1_before.rotation}°")
        print(f"   R2: {r2_before.value}")
        print(f"   C1: {c1_before.value}")
        print(f"   Power: {sorted(power_before.keys())}")
        print(f"   Labels: {sorted(labels_before.keys())}")

        # =====================================================================
        # STEP 2: Update R1 value to 47k and regenerate
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Update R1 value to 47k and verify preservation")
        print("="*70)

        # Modify R1 value: 10k → 47k
        modified_code = original_code.replace(
            'value="10k",',
            'value="47k",'
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        # Regenerate
        result = subprocess.run(
            ["uv", "run", "python", str(python_file)],
            cwd=fixture_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 2 failed: Regeneration with R1=47k\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Verify all components still present
        components_after = verify_components(
            schematic_file,
            expected_refs={"R1", "R2", "C1"},
            message="Step 2: Components"
        )

        power_after = verify_power_symbols(
            schematic_file,
            expected_power={"VCC", "GND"},
            message="Step 2: Power"
        )

        labels_after = verify_labels(
            schematic_file,
            expected_labels={"DATA", "CLK"},
            message="Step 2: Labels"
        )

        # Verify R1 value changed
        verify_component_properties(
            components_after["R1"],
            expected_ref="R1",
            expected_value="47k",
            expected_footprint="0603",
            expected_symbol="Device:R",
            message="Step 2: R1 updated"
        )

        # Verify R1 position and rotation preserved
        assert components_after["R1"].position == r1_before.position, (
            f"R1 position changed:\n"
            f"  Before: {r1_before.position}\n"
            f"  After:  {components_after['R1'].position}"
        )

        assert components_after["R1"].rotation == r1_before.rotation, (
            f"R1 rotation changed:\n"
            f"  Before: {r1_before.rotation}°\n"
            f"  After:  {components_after['R1'].rotation}°"
        )

        # Verify R2 completely unchanged
        from fixtures.helpers import verify_component_unchanged
        verify_component_unchanged(
            r2_before,
            components_after["R2"],
            message="R2 preservation"
        )

        # Verify C1 completely unchanged
        verify_component_unchanged(
            c1_before,
            components_after["C1"],
            message="C1 preservation"
        )

        # Verify synchronization log shows "Update: R1"
        from fixtures.helpers import verify_sync_log
        verify_sync_log(
            result.stdout,
            expected_operation="Update",
            expected_ref="R1",
            message="Step 2: Sync log"
        )

        print(f"✅ Step 2: R1 value updated, all others preserved")
        print(f"   R1: {r1_before.value} → {components_after['R1'].value} ✓")
        print(f"   R1 position: {components_after['R1'].position} (preserved)")
        print(f"   R1 rotation: {components_after['R1'].rotation}° (preserved)")
        print(f"   R2: {components_after['R2'].value} (unchanged)")
        print(f"   C1: {components_after['C1'].value} (unchanged)")
        print(f"   Power: {sorted(power_after.keys())} (preserved)")
        print(f"   Labels: {sorted(labels_after.keys())} (preserved)")

        print(f"\n{'='*70}")
        print(f"🎉 TEST 11 PASSED: Value update preserves all other elements")
        print(f"{'='*70}\n")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
