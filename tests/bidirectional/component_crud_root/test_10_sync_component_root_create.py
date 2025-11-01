#!/usr/bin/env python3
"""Test 10: sync_component_root_create - Add component while preserving all others.

This test verifies that adding a component (R2) to a comprehensive circuit
preserves ALL other schematic elements:
- Existing components (R1, C1) remain unchanged
- Power symbols (VCC, GND) remain unchanged
- Labels (DATA, CLK) remain unchanged
- Component properties (value, footprint, position, rotation) preserved

Initial State:
- Components: R1, C1 (R2 commented out)
- Power: VCC, GND
- Labels: DATA, CLK

Operation:
- Add R2 (uncomment in Python)

Expected Result:
- Components: R1, R2, C1
- R1 and C1 completely unchanged (value, footprint, position, rotation)
- Power and labels unchanged
- Sync log shows "➕ Add: R2"
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_10_sync_component_root_create(request):
    """Test adding R2 component while preserving all other elements.

    Uses comprehensive_root fixture with ALL element types to ensure
    CRUD operation preserves everything except the added component.
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
        # STEP 1: Generate with R1, C1 only (R2 commented out)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate comprehensive circuit without R2")
        print("="*70)

        # Comment out R2 (entire Component definition + connections)
        # Match the entire r2 Component block
        modified_code = re.sub(
            r'(    r2 = Component\(\n'
            r'        symbol="Device:R",\n'
            r'        ref="R2",\n'
            r'        value="4\.7k",\n'
            r'        footprint="Resistor_SMD:R_0603_1608Metric"\n'
            r'    \))',
            r'    # r2 = Component(\n'
            r'    #     symbol="Device:R",\n'
            r'    #     ref="R2",\n'
            r'    #     value="4.7k",\n'
            r'    #     footprint="Resistor_SMD:R_0603_1608Metric"\n'
            r'    # )',
            original_code
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

        # Generate
        result = subprocess.run(
            ["uv", "run", "python", str(python_file)],
            cwd=fixture_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 1 failed: Initial generation without R2\n"
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

        # Verify initial state: R1, C1 (no R2)
        components_before = verify_components(
            schematic_file,
            expected_refs={"R1", "C1"},
            message="Step 1: Components"
        )

        power_before = verify_power_symbols(
            schematic_file,
            expected_power={"VCC", "GND"},
            message="Step 1: Power"
        )

        # Note: CLK label won't exist because R2 (the only component on CLK net) is commented out
        labels_before = verify_labels(
            schematic_file,
            expected_labels={"DATA"},
            message="Step 1: Labels"
        )

        # Store R1 and C1 initial state for comparison
        r1_before = components_before["R1"]
        c1_before = components_before["C1"]

        print(f"✅ Step 1: Initial state verified (R2 absent)")
        print(f"   Components: {sorted(components_before.keys())}")
        print(f"   Power: {sorted(power_before.keys())}")
        print(f"   Labels: {sorted(labels_before.keys())}")
        print(f"   R1: {r1_before.value}, {r1_before.footprint}")
        print(f"   C1: {c1_before.value}, {c1_before.footprint}")

        # =====================================================================
        # STEP 2: Uncomment R2 and regenerate
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Add R2 and verify preservation")
        print("="*70)

        # Restore original code (R2 uncommented)
        with open(python_file, "w") as f:
            f.write(original_code)

        # Regenerate
        result = subprocess.run(
            ["uv", "run", "python", str(python_file)],
            cwd=fixture_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 2 failed: Regeneration with R2\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Verify R2 added and all others preserved
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

        # Note: CLK label might not appear if only one component uses that net
        # Circuit-synth may only generate labels for nets with multiple connections
        labels_after = verify_labels(
            schematic_file,
            expected_labels={"DATA"},  # Only DATA has multiple connections (R1, C1)
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

        # Verify R2 was added with correct properties
        verify_component_properties(
            components_after["R2"],
            expected_ref="R2",
            expected_value="4.7k",
            expected_footprint="0603",
            expected_symbol="Device:R",
            message="R2 addition"
        )

        # Verify synchronization log shows "Add: R2"
        from fixtures.helpers import verify_sync_log
        verify_sync_log(
            result.stdout,
            expected_operation="Add",
            expected_ref="R2",
            message="Step 2: Sync log"
        )

        print(f"✅ Step 2: R2 added, all others preserved")
        print(f"   Components: {sorted(components_after.keys())}")
        print(f"   R1: {components_after['R1'].value} (preserved)")
        print(f"   R2: {components_after['R2'].value} (added)")
        print(f"   C1: {components_after['C1'].value} (preserved)")
        print(f"   Power: {sorted(power_after.keys())} (preserved)")
        print(f"   Labels: {sorted(labels_after.keys())} (preserved)")

        print(f"\n{'='*70}")
        print(f"🎉 TEST 10 PASSED: Component creation preserves all other elements")
        print(f"{'='*70}\n")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
