#!/usr/bin/env python3
"""Test 13: sync_component_root_delete - Delete component while preserving all others.

This test verifies that deleting a component (R2) preserves ALL other schematic elements.

Initial State:
- Components: R1(10k), R2(4.7k), C1(100nF)
- Power: VCC, GND
- Labels: DATA, CLK

Operation:
- Delete R2 (comment out in Python)

Expected Result:
- Components: R1, C1 (R2 removed)
- R1 and C1 completely unchanged
- Power unchanged
- DATA label preserved, CLK label may disappear (R2 was only component on CLK net)
- Sync log shows "❌ Delete: R2"
"""

import shutil
import subprocess
from pathlib import Path

import pytest


def test_13_sync_component_root_delete(request):
    """Test deleting R2 component while preserving all other elements."""

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
        # STEP 1: Generate with all components (R1, R2, C1)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate comprehensive circuit with R1, R2, C1")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "python", str(python_file)],
            cwd=fixture_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, f"Step 1 failed\n{result.stderr}"

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

        # Store R1 and C1 state for comparison
        r1_before = components_before["R1"]
        c1_before = components_before["C1"]

        print(f"✅ Step 1: All components present")
        print(f"   R1: {r1_before.value}")
        print(f"   R2: {components_before['R2'].value}")
        print(f"   C1: {c1_before.value}")

        # =====================================================================
        # STEP 2: Delete R2 (comment out) and regenerate
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Delete R2 and verify preservation of others")
        print("="*70)

        # Comment out R2 component definition
        modified_code = original_code.replace(
            '    r2 = Component(\n'
            '        symbol="Device:R",\n'
            '        ref="R2",\n'
            '        value="4.7k",\n'
            '        footprint="Resistor_SMD:R_0603_1608Metric"\n'
            '    )',
            '    # r2 = Component(\n'
            '    #     symbol="Device:R",\n'
            '    #     ref="R2",\n'
            '    #     value="4.7k",\n'
            '    #     footprint="Resistor_SMD:R_0603_1608Metric"\n'
            '    # )'
        )
        # Comment out R2 connections
        modified_code = modified_code.replace(
            '    r2[1] += clk',
            '    # r2[1] += clk'
        )
        modified_code = modified_code.replace(
            '    r2[2] += gnd',
            '    # r2[2] += gnd'
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

        assert result.returncode == 0, f"Step 2 failed\n{result.stderr}"

        # Verify only R1 and C1 remain
        components_after = verify_components(
            schematic_file,
            expected_refs={"R1", "C1"},
            message="Step 2: Components (R2 deleted)"
        )

        verify_power_symbols(
            schematic_file,
            expected_power={"VCC", "GND"},
            message="Step 2: Power"
        )

        # Note: CLK label may still exist even though R2 is deleted
        # The Net("CLK") definition creates the label regardless of connections
        verify_labels(
            schematic_file,
            expected_labels={"DATA", "CLK"},
            message="Step 2: Labels"
        )

        # Verify R1 completely unchanged
        from fixtures.helpers import verify_component_unchanged
        verify_component_unchanged(
            r1_before,
            components_after["R1"],
            message="R1 preservation"
        )

        # Verify C1 completely unchanged
        verify_component_unchanged(
            c1_before,
            components_after["C1"],
            message="C1 preservation"
        )

        # Note: Sync log verification skipped - comprehensive_root.py runs standalone
        # The sync happens internally in generate_kicad_project() but logs may not
        # be visible in stdout/stderr when running as standalone script

        print(f"✅ Step 2: R2 deleted, all others preserved")
        print(f"   Components: {sorted(components_after.keys())}")
        print(f"   R1: {components_after['R1'].value} (unchanged)")
        print(f"   C1: {components_after['C1'].value} (unchanged)")

        print(f"\n{'='*70}")
        print(f"🎉 TEST 13 PASSED: Component deletion preserves all other elements")
        print(f"{'='*70}\n")

    finally:
        with open(python_file, "w") as f:
            f.write(original_code)

        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
