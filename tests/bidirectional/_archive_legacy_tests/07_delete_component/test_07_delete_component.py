#!/usr/bin/env python3
"""
Automated test for 07_delete_component bidirectional test.

Tests deleting component in Python → regenerating KiCad schematic.
This tests Python-side deletion (counterpart to 07_b which tests KiCad side deletion).

Workflow:
1. Generate KiCad with both R1 and R2
2. Comment out R2 in Python
3. Regenerate KiCad
4. Validate schematic only has R1 (R2 removed)
5. Verify synchronization logs show "Remove: R2"

Validation uses kicad-sch-api.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_07_delete_component(request):
    """Test deleting component in Python → syncs to KiCad.

    Workflow:
    1. Generate KiCad with R1 and R2
    2. Comment out R2 in Python (deletion)
    3. Regenerate KiCad
    4. Validate schematic only has R1 (R2 removed)
    5. Verify sync logs show "Remove: R2"

    This tests Python → KiCad deletion sync.

    Level 2 Semantic Validation:
    - kicad-sch-api for schematic validation
    - Sync log validation for deletion detection
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "two_resistors.py"
    output_dir = test_dir / "two_resistors"
    schematic_file = output_dir / "two_resistors.kicad_sch"

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
        # STEP 1: Generate KiCad with both R1 and R2
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with R1 and R2")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "two_resistors.py"],
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

        # Validate both R1 and R2 in schematic
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 2, (
            f"Step 1: Expected 2 components, found {len(components)}"
        )

        refs = {c.reference for c in components}
        assert "R1" in refs and "R2" in refs

        print(f"✅ Step 1: KiCad generated with R1 and R2")

        # =====================================================================
        # STEP 2: Comment out R2 in Python (delete)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Comment out R2 in Python (deletion)")
        print("="*70)

        # Comment out R2 block
        modified_code = re.sub(
            r'(\s*)r2 = Component\(',
            r'\1# r2 = Component(',
            original_code,
            count=1
        )
        # Comment out all lines in R2 definition
        modified_code = re.sub(
            r'(# r2 = Component\(.*?\n)(.*?)(    \))',
            lambda m: m.group(1) + '\n'.join(
                '    #' + line if not line.strip().startswith('#') else line
                for line in m.group(2).split('\n')
            ) + '\n    # ' + m.group(3).strip(),
            modified_code,
            flags=re.DOTALL
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 2: R2 commented out in Python")

        # =====================================================================
        # STEP 3: Regenerate KiCad (should remove R2)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Regenerate KiCad (should remove R2)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "two_resistors.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 3 failed: Regeneration after deleting R2\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Validate only R1 in schematic (R2 removed)
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 1, (
            f"Step 3: Expected 1 component (R1 only), found {len(components)}"
        )

        assert components[0].reference == "R1", (
            f"Expected R1, got {components[0].reference}"
        )

        # Validate synchronization log shows "Remove: R2"
        assert "⚠️  Remove: R2" in result.stdout or "Remove: R2" in result.stdout, (
            f"Expected synchronization log showing 'Remove: R2'\n"
            f"STDOUT:\n{result.stdout}"
        )

        print(f"✅ Step 3: R2 removed from schematic")
        print(f"   - Only R1 remains: {components[0].reference}")
        print(f"   - Synchronization detected deletion")

    finally:
        # Restore original Python file (both R1 and R2)
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
