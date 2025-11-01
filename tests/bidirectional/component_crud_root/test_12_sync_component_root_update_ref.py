#!/usr/bin/env python3
"""Test 12: sync_component_root_update_ref - Rename component reference while preserving all others.

This test verifies that renaming a component reference (R1 → R10) preserves
ALL other schematic elements and the component's properties.

Initial State:
- Components: R1(10k), R2(4.7k), C1(100nF)
- Power: VCC, GND
- Labels: DATA, CLK

Operation:
- Rename R1 → R10

Expected Result:
- Component now named R10 with same value (10k), footprint, position, rotation
- R2 and C1 completely unchanged
- Power and labels unchanged
- Sync log shows "Update: R1" or "Delete: R1" + "Add: R10"
"""

import shutil
import subprocess
from pathlib import Path

import pytest


def test_12_sync_component_root_update_ref(request):
    """Test renaming R1 → R10 while preserving all properties and other elements."""

    # Setup paths
    test_dir = Path(__file__).parent
    fixture_dir = test_dir.parent / "fixtures"
    python_file = fixture_dir / "comprehensive_root.py"
    output_dir = fixture_dir / "comprehensive_root"
    schematic_file = output_dir / "comprehensive_root.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    if output_dir.exists():
        shutil.rmtree(output_dir)

    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate with R1
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate comprehensive circuit with R1")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "python", str(python_file)],
            cwd=fixture_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 1 failed\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        import sys
        sys.path.insert(0, str(test_dir.parent))
        from fixtures.helpers import (
            verify_components,
            verify_power_symbols,
            verify_labels,
        )

        components_before = verify_components(
            schematic_file,
            expected_refs={"R1", "R2", "C1"},
            message="Step 1: Components"
        )

        # Store R1 properties
        r1_before = components_before["R1"]
        r1_value = r1_before.value
        r1_footprint = r1_before.footprint
        r1_lib_id = r1_before.lib_id
        r1_position = r1_before.position
        r1_rotation = r1_before.rotation

        r2_before = components_before["R2"]
        c1_before = components_before["C1"]

        print(f"✅ Step 1: Initial state verified")
        print(f"   R1: {r1_value} @ {r1_position}, {r1_rotation}°")

        # =====================================================================
        # STEP 2: Rename R1 → R10 and regenerate
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Rename R1 → R10 and verify preservation")
        print("="*70)

        # Rename R1 → R10
        modified_code = original_code.replace(
            'ref="R1"',
            'ref="R10"'
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        result = subprocess.run(
            ["uv", "run", "python", str(python_file)],
            cwd=fixture_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 2 failed\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Verify R10 exists, R1 doesn't
        components_after = verify_components(
            schematic_file,
            expected_refs={"R10", "R2", "C1"},
            message="Step 2: Components"
        )

        verify_power_symbols(
            schematic_file,
            expected_power={"VCC", "GND"},
            message="Step 2: Power"
        )

        verify_labels(
            schematic_file,
            expected_labels={"DATA", "CLK"},
            message="Step 2: Labels"
        )

        # Verify R10 has same properties as R1
        r10_after = components_after["R10"]
        assert r10_after.value == r1_value, f"Value changed: {r1_value} → {r10_after.value}"
        assert r10_after.footprint == r1_footprint, f"Footprint changed"
        assert r10_after.lib_id == r1_lib_id, f"Lib ID changed"
        assert r10_after.position == r1_position, f"Position changed: {r1_position} → {r10_after.position}"
        assert r10_after.rotation == r1_rotation, f"Rotation changed: {r1_rotation}° → {r10_after.rotation}°"

        # Verify R2 and C1 unchanged
        from fixtures.helpers import verify_component_unchanged
        verify_component_unchanged(
            r2_before,
            components_after["R2"],
            message="R2 preservation"
        )
        verify_component_unchanged(
            c1_before,
            components_after["C1"],
            message="C1 preservation"
        )

        print(f"✅ Step 2: R1 → R10 renamed, all properties and others preserved")
        print(f"   R10: {r10_after.value} @ {r10_after.position} ✓")
        print(f"   R2: {components_after['R2'].value} (unchanged)")
        print(f"   C1: {components_after['C1'].value} (unchanged)")

        print(f"\n{'='*70}")
        print(f"🎉 TEST 12 PASSED: Reference rename preserves all properties")
        print(f"{'='*70}\n")

    finally:
        with open(python_file, "w") as f:
            f.write(original_code)

        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
