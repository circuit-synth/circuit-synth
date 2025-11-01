#!/usr/bin/env python3
"""
Automated test for 03_python_to_kicad bidirectional test.

Tests incremental component addition: Python → KiCad with component commented out,
then uncommented to verify bidirectional sync detects and adds the component.

This is a critical workflow: starting with blank circuit, adding components
incrementally, and verifying KiCad schematic updates correctly.

Validation Level 2 (Semantic): Uses kicad-sch-api to validate component
properties independent of positioning/formatting.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_03_python_to_kicad_incremental_addition(request):
    """Test incremental component addition via Python → KiCad sync.

    Workflow:
    1. Start with R1 commented out → generates blank circuit
    2. Verify schematic has no components (kicad-sch-api)
    3. Uncomment R1 → regenerate circuit
    4. Verify schematic has exactly 1 resistor with correct properties

    This tests the core bidirectional feature: detecting changes in Python
    and synchronizing them to KiCad schematic.

    Level 2 Semantic Validation:
    - Uses kicad-sch-api to parse schematic
    - Validates component properties (ref, value, footprint)
    - Independent of component position/rotation
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "single_resistor.py"
    output_dir = test_dir / "single_resistor"
    schematic_file = output_dir / "single_resistor.kicad_sch"

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
        # STEP 1: Generate with R1 commented out (should be blank)
        # =====================================================================

        # Ensure R1 is commented out
        commented_code = original_code
        if "# r1 = Component(" not in commented_code:
            # Need to comment out R1
            commented_code = re.sub(
                r'(\s*)r1 = Component\(',
                r'\1# r1 = Component(',
                commented_code
            )
            commented_code = re.sub(
                r'(\s*)#(\s+symbol=)',
                r'\1#\2',
                commented_code
            )
            commented_code = re.sub(
                r'(\s*)#(\s+ref=)',
                r'\1#\2',
                commented_code
            )
            commented_code = re.sub(
                r'(\s*)#(\s+value=)',
                r'\1#\2',
                commented_code
            )
            commented_code = re.sub(
                r'(\s*)#(\s+footprint=)',
                r'\1#\2',
                commented_code
            )
            commented_code = re.sub(
                r'(\s*)#(\s+\))',
                r'\1#\2',
                commented_code
            )
            with open(python_file, "w") as f:
                f.write(commented_code)

        # Run Python file to generate blank circuit
        result = subprocess.run(
            ["uv", "run", "single_resistor.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 1 failed: Python generation with commented R1\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Validate schematic is blank
        assert schematic_file.exists(), "Schematic file not created (step 1)"

        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 0, (
            f"Step 1: Expected blank circuit (R1 commented), found {len(components)} components"
        )

        print("✅ Step 1: Blank circuit generated (R1 commented out)")

        # =====================================================================
        # STEP 2: Uncomment R1 and regenerate
        # =====================================================================

        # Uncomment R1
        uncommented_code = re.sub(
            r'(\s*)# r1 = Component\(',
            r'\1r1 = Component(',
            original_code
        )
        uncommented_code = re.sub(
            r'(\s*)#(\s+)(symbol=)',
            r'\1\2\3',
            uncommented_code
        )
        uncommented_code = re.sub(
            r'(\s*)#(\s+)(ref=)',
            r'\1\2\3',
            uncommented_code
        )
        uncommented_code = re.sub(
            r'(\s*)#(\s+)(value=)',
            r'\1\2\3',
            uncommented_code
        )
        uncommented_code = re.sub(
            r'(\s*)#(\s+)(footprint=)',
            r'\1\2\3',
            uncommented_code
        )
        uncommented_code = re.sub(
            r'(\s*)#(\s+)(\))',
            r'\1\2\3',
            uncommented_code
        )

        with open(python_file, "w") as f:
            f.write(uncommented_code)

        # Run Python file again to add R1
        result = subprocess.run(
            ["uv", "run", "single_resistor.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 2 failed: Python generation with uncommented R1\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Validate schematic has R1
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 1, (
            f"Step 2: Expected 1 component (R1 added), found {len(components)}"
        )

        # Validate R1 properties
        r1 = components[0]

        assert r1.reference == "R1", (
            f"Expected reference 'R1', got '{r1.reference}'"
        )

        assert r1.value == "10k", (
            f"Expected value '10k', got '{r1.value}'"
        )

        assert "R_0603" in r1.footprint, (
            f"Expected footprint containing 'R_0603', got '{r1.footprint}'"
        )

        # Check logs show synchronization action
        assert "➕ Add: R1" in result.stdout or "Add: R1" in result.stdout, (
            "Expected synchronization log showing 'Add: R1'"
        )

        print("✅ Step 2: R1 added successfully")
        print(f"   - Reference: {r1.reference}")
        print(f"   - Value: {r1.value}")
        print(f"   - Footprint: {r1.footprint}")
        print(f"   - Synchronization detected and logged")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
