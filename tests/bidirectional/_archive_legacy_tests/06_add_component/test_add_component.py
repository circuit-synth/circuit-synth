#!/usr/bin/env python3
"""
Automated test for 06_add_component bidirectional test.

Tests adding component in Python → regenerating KiCad schematic.
Similar to test 03 but focuses on component addition workflow.

Validation uses kicad-sch-api to verify components present.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_06_add_component(request):
    """Test adding component in Python → syncs to KiCad.

    Workflow:
    1. Start with R1 only (R2 commented out)
    2. Generate KiCad from Python → validate R1 only
    3. Uncomment R2 in Python
    4. Regenerate KiCad → validate both R1 and R2 present
    5. Verify synchronization logs show "Add: R2"

    Level 2 Semantic Validation:
    - kicad-sch-api for schematic component validation
    - Sync log validation for detecting addition
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
        # STEP 1: Generate with R1 only (R2 commented)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with R1 only")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "single_resistor.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 1 failed: Initial generation with R1\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Schematic not created"

        # Validate only R1 in schematic
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 1, (
            f"Step 1: Expected 1 component (R1), found {len(components)}"
        )
        assert components[0].reference == "R1"
        assert components[0].value == "10k"

        print(f"✅ Step 1: KiCad generated with R1 only")
        print(f"   - Reference: {components[0].reference}")
        print(f"   - Value: {components[0].value}")

        # =====================================================================
        # STEP 2: Uncomment R2 and regenerate
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Uncomment R2 and regenerate")
        print("="*70)

        # Uncomment R2
        modified_code = re.sub(
            r'# r2 = Component\(',
            r'r2 = Component(',
            original_code,
            count=1
        )
        modified_code = re.sub(
            r'#(\s+)(symbol=|ref=|value=|footprint=|\))',
            r'\1\2',
            modified_code
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        # Regenerate
        result = subprocess.run(
            ["uv", "run", "single_resistor.py"],
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

        # Validate both R1 and R2 in schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 2, (
            f"Step 2: Expected 2 components (R1, R2), found {len(components)}"
        )

        refs = {c.reference for c in components}
        assert "R1" in refs and "R2" in refs, (
            f"Expected R1 and R2, found {refs}"
        )

        # Validate R1 preserved
        r1 = next(c for c in components if c.reference == "R1")
        assert r1.value == "10k"

        # Validate R2 added
        r2 = next(c for c in components if c.reference == "R2")
        assert r2.value == "10k"

        # Validate synchronization log shows "Add: R2"
        assert "➕ Add: R2" in result.stdout or "Add: R2" in result.stdout, (
            f"Expected synchronization log showing 'Add: R2'\n"
            f"STDOUT:\n{result.stdout}"
        )

        print(f"✅ Step 2: Both components present after regeneration")
        print(f"   - R1: {r1.value} (preserved)")
        print(f"   - R2: {r2.value} (added)")
        print(f"   - Synchronization detected addition")

    finally:
        # Restore original Python file (R2 commented out)
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
