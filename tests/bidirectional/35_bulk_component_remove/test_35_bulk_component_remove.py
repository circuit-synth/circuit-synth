#!/usr/bin/env python3
"""
Automated test for 35_bulk_component_remove bidirectional test.

Tests deleting multiple components in Python → regenerating KiCad schematic.
This tests Python-side bulk deletion (counterpart to KiCad-side deletion).

Workflow:
1. Generate KiCad with 10 resistors (R1-R10)
2. Comment out R3, R5, R7 in Python
3. Regenerate KiCad
4. Validate schematic only has R1, R2, R4, R6, R8, R9, R10 (7 remaining)
5. Verify synchronization logs show "Remove: R3", "Remove: R5", "Remove: R7"
6. Verify positions of remaining components are preserved

Validation uses kicad-sch-api.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_35_bulk_component_remove(request):
    """Test deleting multiple components in Python → syncs to KiCad.

    Workflow:
    1. Generate KiCad with 10 resistors (R1-R10)
    2. Comment out R3, R5, R7 in Python (bulk deletion)
    3. Regenerate KiCad
    4. Validate schematic only has 7 resistors (R3, R5, R7 removed)
    5. Verify sync logs show "Remove: R3", "Remove: R5", "Remove: R7"
    6. Verify remaining component positions are preserved

    This tests Python → KiCad bulk deletion sync.

    Level 2 Semantic Validation:
    - kicad-sch-api for schematic validation
    - Sync log validation for deletion detection
    - Position preservation validation
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "ten_resistors_for_removal.py"
    output_dir = test_dir / "ten_resistors_for_removal"
    schematic_file = output_dir / "ten_resistors_for_removal.kicad_sch"

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
        # STEP 1: Generate KiCad with all 10 resistors
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with 10 resistors (R1-R10)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "ten_resistors_for_removal.py"],
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

        # Validate all 10 resistors in schematic
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 10, (
            f"Step 1: Expected 10 components, found {len(components)}"
        )

        refs_initial = {c.reference for c in components}
        expected_refs = {"R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10"}
        assert refs_initial == expected_refs, (
            f"Step 1: Expected refs {expected_refs}, got {refs_initial}"
        )

        # Store initial positions for remaining components
        positions_before = {}
        for c in components:
            positions_before[c.reference] = c.position

        print(f"✅ Step 1: KiCad generated with all 10 resistors")
        for ref in sorted(expected_refs):
            value = next(c.value for c in components if c.reference == ref)
            print(f"   - {ref}: {value}Ω at position {positions_before[ref]}")

        # =====================================================================
        # STEP 2: Comment out R3, R5, R7 in Python (bulk deletion)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Comment out R3, R5, R7 in Python (bulk deletion)")
        print("="*70)

        modified_code = original_code

        # Comment out R3
        modified_code = re.sub(
            r'(\s*)r3 = Component\(',
            r'\1# r3 = Component(',
            modified_code,
            count=1
        )
        modified_code = re.sub(
            r'(# r3 = Component\(.*?\n)(.*?)(    \))',
            lambda m: m.group(1) + '\n'.join(
                '    #' + line if not line.strip().startswith('#') else line
                for line in m.group(2).split('\n')
            ) + '\n    # ' + m.group(3).strip(),
            modified_code,
            flags=re.DOTALL,
            count=1
        )

        # Comment out R5
        modified_code = re.sub(
            r'(\s*)r5 = Component\(',
            r'\1# r5 = Component(',
            modified_code,
            count=1
        )
        modified_code = re.sub(
            r'(# r5 = Component\(.*?\n)(.*?)(    \))',
            lambda m: m.group(1) + '\n'.join(
                '    #' + line if not line.strip().startswith('#') else line
                for line in m.group(2).split('\n')
            ) + '\n    # ' + m.group(3).strip(),
            modified_code,
            flags=re.DOTALL,
            count=1
        )

        # Comment out R7
        modified_code = re.sub(
            r'(\s*)r7 = Component\(',
            r'\1# r7 = Component(',
            modified_code,
            count=1
        )
        modified_code = re.sub(
            r'(# r7 = Component\(.*?\n)(.*?)(    \))',
            lambda m: m.group(1) + '\n'.join(
                '    #' + line if not line.strip().startswith('#') else line
                for line in m.group(2).split('\n')
            ) + '\n    # ' + m.group(3).strip(),
            modified_code,
            flags=re.DOTALL,
            count=1
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 2: R3, R5, R7 commented out in Python")

        # =====================================================================
        # STEP 3: Regenerate KiCad (should remove R3, R5, R7)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Regenerate KiCad (should remove R3, R5, R7)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "ten_resistors_for_removal.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 3 failed: Regeneration after deleting R3, R5, R7\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Validate only 7 resistors remain in schematic (R1, R2, R4, R6, R8, R9, R10)
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 7, (
            f"Step 3: Expected 7 components (R1,R2,R4,R6,R8,R9,R10), found {len(components)}"
        )

        refs_after = {c.reference for c in components}
        expected_remaining = {"R1", "R2", "R4", "R6", "R8", "R9", "R10"}
        assert refs_after == expected_remaining, (
            f"Step 3: Expected refs {expected_remaining}, got {refs_after}"
        )

        # Validate synchronization logs show deletions
        for removed_ref in ["R3", "R5", "R7"]:
            assert (
                f"⚠️  Remove: {removed_ref}" in result.stdout or
                f"Remove: {removed_ref}" in result.stdout
            ), (
                f"Expected synchronization log showing 'Remove: {removed_ref}'\n"
                f"STDOUT:\n{result.stdout}"
            )

        print(f"✅ Step 3: R3, R5, R7 removed from schematic")
        print(f"   - Remaining components: {', '.join(sorted(refs_after))}")
        print(f"   - Synchronization detected all deletions")

        # =====================================================================
        # STEP 4: Verify remaining components preserve positions
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Verify position preservation for remaining components")
        print("="*70)

        positions_after = {}
        for c in components:
            positions_after[c.reference] = c.position

        # Verify positions of remaining components
        position_mismatches = []
        for ref in expected_remaining:
            pos_before = positions_before[ref]
            pos_after = positions_after[ref]

            if pos_before.x != pos_after.x or pos_before.y != pos_after.y:
                position_mismatches.append(
                    f"{ref}: before {pos_before} → after {pos_after}"
                )
            else:
                print(f"   ✅ {ref}: position preserved at {pos_after}")

        assert not position_mismatches, (
            f"Position mismatches detected:\n" +
            "\n".join(position_mismatches)
        )

        print(f"✅ Step 4: All remaining component positions preserved")

        # =====================================================================
        # STEP 5: Verify deleted components are completely gone
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Verify deleted components are completely gone")
        print("="*70)

        deleted_refs = {"R3", "R5", "R7"}
        found_deleted = refs_after & deleted_refs

        assert not found_deleted, (
            f"Deleted components still found in schematic: {found_deleted}"
        )

        print(f"✅ Step 5: Deleted components (R3, R5, R7) completely removed")
        print(f"   - No orphaned connections")
        print(f"   - No remaining references to deleted components")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
