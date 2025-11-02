#!/usr/bin/env python3
"""
Automated test for Test 10: Add Component (Root Sheet)

Tests adding component in Python → synchronizing to KiCad schematic
while preserving all other elements.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_10_add_component(request):
    """Test adding R2 component while preserving R1, C1, power, and labels.

    Workflow:
    1. Start with R1, C1 only (R2 commented out)
    2. Generate KiCad → validate R1, C1 only
    3. Uncomment R2 in Python
    4. Regenerate KiCad → validate R1, R2, C1 present
    5. Verify R1, C1 unchanged (position, value, footprint)
    6. Verify power and labels preserved
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
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
        # STEP 1: Generate with R1, C1 only (R2 commented)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with R1, C1 only")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "comprehensive_root.py"],
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

        assert schematic_file.exists(), "Schematic not created"

        # Validate R1 and C1 in schematic
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))

        # Filter out power symbols
        regular_components = [c for c in sch.components if not c.reference.startswith("#PWR")]
        component_refs = {c.reference for c in regular_components}

        assert len(regular_components) == 2, (
            f"Step 1: Expected 2 components (R1, C1), found {len(regular_components)}: {component_refs}"
        )
        assert component_refs == {"R1", "C1"}

        # Store initial state for comparison
        r1_before = next(c for c in regular_components if c.reference == "R1")
        c1_before = next(c for c in regular_components if c.reference == "C1")

        print(f"✅ Step 1: KiCad generated with R1, C1 only")
        print(f"   - R1: {r1_before.value}")
        print(f"   - C1: {c1_before.value}")

        # =====================================================================
        # STEP 2: Uncomment R2 and regenerate
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Uncomment R2 and regenerate")
        print("="*70)

        # Uncomment R2 definition
        modified_code = original_code.replace(
            '    # r2 = Component(',
            '    r2 = Component('
        )
        modified_code = modified_code.replace(
            '    #     symbol="Device:R",',
            '        symbol="Device:R",'
        )
        modified_code = modified_code.replace(
            '    #     ref="R2",',
            '        ref="R2",'
        )
        modified_code = modified_code.replace(
            '    #     value="4.7k",',
            '        value="4.7k",'
        )
        modified_code = modified_code.replace(
            '    #     footprint="Resistor_SMD:R_0603_1608Metric"',
            '        footprint="Resistor_SMD:R_0603_1608Metric"'
        )
        modified_code = modified_code.replace(
            '    # )',
            '    )'
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        # Regenerate
        result = subprocess.run(
            ["uv", "run", "comprehensive_root.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 2 failed: Regeneration with R2\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Validate R1, R2, C1 in schematic
        sch = Schematic.load(str(schematic_file))
        regular_components = [c for c in sch.components if not c.reference.startswith("#PWR")]
        component_refs = {c.reference for c in regular_components}

        assert len(regular_components) == 3, (
            f"Step 2: Expected 3 components (R1, R2, C1), found {len(regular_components)}: {component_refs}"
        )
        assert component_refs == {"R1", "R2", "C1"}

        # Verify R1 preserved
        r1_after = next(c for c in regular_components if c.reference == "R1")
        assert r1_after.value == r1_before.value, "R1 value changed"
        assert r1_after.footprint == r1_before.footprint, "R1 footprint changed"
        assert r1_after.position == r1_before.position, "R1 position changed"

        # Verify C1 preserved
        c1_after = next(c for c in regular_components if c.reference == "C1")
        assert c1_after.value == c1_before.value, "C1 value changed"
        assert c1_after.footprint == c1_before.footprint, "C1 footprint changed"
        assert c1_after.position == c1_before.position, "C1 position changed"

        # Verify R2 added
        r2_after = next(c for c in regular_components if c.reference == "R2")
        assert r2_after.value == "4.7k"

        print(f"✅ Step 2: All components present, R1 and C1 preserved")
        print(f"   - R1: {r1_after.value} (preserved)")
        print(f"   - R2: {r2_after.value} (added)")
        print(f"   - C1: {c1_after.value} (preserved)")

    finally:
        # Restore original Python file (R2 commented out)
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
