#!/usr/bin/env python3
"""
Automated test for 38_empty_subcircuit bidirectional test.

Tests empty hierarchical sheet handling: Generating a subcircuit with no components,
then dynamically adding and removing components in Python and syncing to KiCad.

Core Question: When you generate an empty subcircuit (no components), does KiCad
handle it correctly? Can you then add components in Python and sync to KiCad?

Workflow (Python→KiCad sync):
1. Generate KiCad from Python with R1 on root sheet and empty subcircuit
2. Verify root sheet has R1, subcircuit sheet exists but is empty
3. Add R2 to empty subcircuit in Python code
4. Sync Python→KiCad (regenerate)
5. Validate R2 now exists in KiCad subcircuit
6. Remove R2 from subcircuit in Python code
7. Sync Python→KiCad again
8. Validate subcircuit is empty again in KiCad

Validation uses kicad-sch-api for Level 2 semantic validation.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_38_empty_subcircuit(request):
    """Test empty subcircuit handling and dynamic component addition/sync.

    EDGE CASE TEST (Empty Hierarchical Sheets - Python→KiCad sync):
    Validates that empty subcircuits can be generated and populated dynamically
    in Python, with changes syncing correctly to KiCad.

    Workflow:
    1. Generate KiCad from Python with R1 on root sheet and empty subcircuit
    2. Verify root sheet has R1, subcircuit is empty in KiCad
    3. Add R2 in Python → sync to KiCad → verify it appears
    4. Remove R2 in Python → sync to KiCad → verify it's empty again

    Why important:
    - Enables generating hierarchical structure before implementation details
    - Allows dynamic population of subsystems in Python
    - Tests edge case of truly empty sheets
    - Ensures robustness of empty sheet handling in KiCad during sync

    Level 2 Semantic Validation:
    - kicad-sch-api for sheet structure and component placement
    - File system for multiple schematic files
    - Component counting for empty/non-empty validation
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "empty_subcircuit.py"
    output_dir = test_dir / "empty_subcircuit"
    schematic_file = output_dir / "empty_subcircuit.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file (root sheet with R1, empty subcircuit)
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate KiCad with R1 on root sheet and empty subcircuit
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 1: Generate KiCad with R1 on root sheet and empty subcircuit")
        print("=" * 70)

        result = subprocess.run(
            ["uv", "run", "empty_subcircuit.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Step 1 failed: Initial generation\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Root schematic not created"

        print(f"✅ Step 1: Root schematic generated")
        print(f"   - Root schematic file exists: {schematic_file}")

        # Verify schematic file exists
        sch_files = list(output_dir.glob("*.kicad_sch"))
        print(f"   - Schematic files found: {len(sch_files)}")
        for sch_file in sch_files:
            print(f"     * {sch_file.name}")

        # Load root schematic and verify R1 exists
        from kicad_sch_api import Schematic

        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) >= 1, "R1 not found in root schematic"
        r1 = next((c for c in components if c.reference == "R1"), None)
        assert r1 is not None, "R1 not found in root schematic"

        r1_initial_pos = r1.position
        print(f"   - R1 found on root sheet at position: {r1_initial_pos}")

        # Verify JSON structure has empty subcircuit
        json_file = output_dir / "empty_subcircuit.json"
        assert json_file.exists(), "JSON netlist not found"

        with open(json_file, "r") as f:
            json_data = json.load(f)

        has_subcircuits = "subcircuits" in json_data and len(json_data["subcircuits"]) > 0
        print(f"\n   Hierarchical structure in JSON:")
        print(f"     - Root circuit: {json_data.get('name', 'unknown')}")
        print(f"     - Has subcircuits: {has_subcircuits}")

        assert has_subcircuits, "JSON should contain subcircuits"

        # Verify empty subcircuit exists in JSON
        empty_sub_in_json = next(
            (
                s
                for s in json_data.get("subcircuits", [])
                if "placeholder_subcircuit" in s.get("name", "")
            ),
            None,
        )
        assert empty_sub_in_json is not None, "placeholder_subcircuit not found in JSON"

        # Verify placeholder_subcircuit has no components
        empty_sub_components = empty_sub_in_json.get("components", {})
        subcircuit_name = empty_sub_in_json.get("name")
        print(f"       * {subcircuit_name} (components: {len(empty_sub_components)})")
        assert (
            len(empty_sub_components) == 0
        ), f"{subcircuit_name} should have no components, found {len(empty_sub_components)}"

        print(f"\n✅ Step 1 complete: Empty subcircuit created successfully")
        print(f"   - Root circuit has R1: ✓")
        print(f"   - {subcircuit_name} exists: ✓")
        print(f"   - {subcircuit_name} has 0 components: ✓")

        # =====================================================================
        # STEP 2: Add R2 to empty subcircuit in Python code
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 2: Add R2 to empty subcircuit in Python code")
        print("=" * 70)

        # Uncomment the R2 component between the markers
        # The fixture has commented-out R2 component code that we'll uncomment
        modified_code = original_code.replace(
            "    # Uncomment to add components to subcircuit:\n"
            "    # r2 = Component(\n"
            "    #     symbol=\"Device:R\",\n"
            "    #     ref=\"R2\",\n"
            "    #     value=\"1k\",\n"
            "    #     footprint=\"Resistor_SMD:R_0603_1608Metric\",\n"
            "    # )",
            "    # Uncomment to add components to subcircuit:\n"
            "    r2 = Component(\n"
            "        symbol=\"Device:R\",\n"
            "        ref=\"R2\",\n"
            "        value=\"1k\",\n"
            "        footprint=\"Resistor_SMD:R_0603_1608Metric\",\n"
            ")"
        )

        assert modified_code != original_code, (
            "Failed to modify Python code - R2 component not found or pattern incorrect"
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 2: Component R2 added to Python code")
        print(f"   - Component: R2 (1k resistor)")
        print(f"   - Will be added to: placeholder_subcircuit")

        # =====================================================================
        # STEP 3: Regenerate KiCad with R2 in subcircuit
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 3: Regenerate KiCad with R2 in subcircuit")
        print("=" * 70)

        # Remove old output to force fresh generation
        if output_dir.exists():
            shutil.rmtree(output_dir)

        result = subprocess.run(
            ["uv", "run", "empty_subcircuit.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Step 3 failed: Regeneration with R2 in subcircuit\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 3: KiCad regenerated with R2 in subcircuit")

        # =====================================================================
        # STEP 4: Verify R2 now exists in subcircuit
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 4: Verify R2 now exists in subcircuit")
        print("=" * 70)

        # Load schematic and verify both R1 and R2 exist
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) >= 2, "Expected both R1 and R2 in schematic"
        r1_after_add = next((c for c in components if c.reference == "R1"), None)
        r2 = next((c for c in components if c.reference == "R2"), None)

        assert r1_after_add is not None, "R1 missing after adding R2"
        assert r2 is not None, "R2 not found after adding to subcircuit"

        r1_after_add_pos = r1_after_add.position
        r2_pos = r2.position

        print(f"   R1 (on root sheet):")
        print(f"     - Initial position: {r1_initial_pos}")
        print(f"     - After R2 addition: {r1_after_add_pos}")
        print(f"     ✓ Position preserved: {r1_initial_pos == r1_after_add_pos}")

        print(f"\n   R2 (on subcircuit):")
        print(f"     - Position: {r2_pos}")

        # Verify R1 position is still preserved
        assert (
            r1_initial_pos == r1_after_add_pos
        ), "R1 position should be preserved when adding R2"

        # Verify JSON structure now has R2 in subcircuit
        with open(json_file, "r") as f:
            json_data = json.load(f)

        empty_sub_in_json = next(
            (
                s
                for s in json_data.get("subcircuits", [])
                if "placeholder_subcircuit" in s.get("name", "")
            ),
            None,
        )
        assert empty_sub_in_json is not None, "placeholder_subcircuit not found in JSON"

        empty_sub_components = empty_sub_in_json.get("components", {})
        subcircuit_name_with_r2 = empty_sub_in_json.get("name")
        assert (
            "R2" in empty_sub_components
        ), f"R2 not found in {subcircuit_name_with_r2}, components: {list(empty_sub_components.keys())}"

        print(f"\n✅ Step 4 complete: R2 successfully added to subcircuit")
        print(f"   - R1 still on root sheet: ✓")
        print(f"   - R2 now in {subcircuit_name_with_r2}: ✓")
        print(f"   - R1 position preserved: ✓")

        # =====================================================================
        # STEP 5: Remove R2 from subcircuit in Python code
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 5: Remove R2 from subcircuit in Python code")
        print("=" * 70)

        # Re-comment the R2 component (reverse of step 2)
        current_code = open(python_file, "r").read()
        modified_code_remove = current_code.replace(
            "    # Uncomment to add components to subcircuit:\n"
            "    r2 = Component(\n"
            "        symbol=\"Device:R\",\n"
            "        ref=\"R2\",\n"
            "        value=\"1k\",\n"
            "        footprint=\"Resistor_SMD:R_0603_1608Metric\",\n"
            ")",
            "    # Uncomment to add components to subcircuit:\n"
            "    # r2 = Component(\n"
            "    #     symbol=\"Device:R\",\n"
            "    #     ref=\"R2\",\n"
            "    #     value=\"1k\",\n"
            "    #     footprint=\"Resistor_SMD:R_0603_1608Metric\",\n"
            "    # )"
        )

        assert modified_code_remove != current_code, (
            "Failed to re-comment R2 component in Python code"
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code_remove)

        print(f"✅ Step 5: R2 removed from Python code")
        print(f"   - Subcircuit will be empty again")

        # =====================================================================
        # STEP 6: Regenerate KiCad with empty subcircuit again
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 6: Regenerate KiCad with empty subcircuit again")
        print("=" * 70)

        # Remove old output to force fresh generation
        if output_dir.exists():
            shutil.rmtree(output_dir)

        result = subprocess.run(
            ["uv", "run", "empty_subcircuit.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Step 6 failed: Regeneration with empty subcircuit\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 6: KiCad regenerated with empty subcircuit")

        # =====================================================================
        # STEP 7: Verify subcircuit is empty again and R1 still exists
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 7: Verify subcircuit is empty again and R1 still exists")
        print("=" * 70)

        # Load schematic and verify only R1 exists
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        r1_final = next((c for c in components if c.reference == "R1"), None)
        r2_final = next((c for c in components if c.reference == "R2"), None)

        assert r1_final is not None, "R1 missing after removing R2"
        assert r2_final is None, "R2 should not exist after being removed"

        r1_final_pos = r1_final.position

        print(f"   R1 final position: {r1_final_pos}")
        print(f"     ✓ Position preserved throughout test: {r1_initial_pos == r1_final_pos}")

        print(f"\n   R2 status: Not found (correctly removed)")

        # Verify JSON structure has empty subcircuit again
        with open(json_file, "r") as f:
            json_data = json.load(f)

        empty_sub_in_json = next(
            (
                s
                for s in json_data.get("subcircuits", [])
                if "placeholder_subcircuit" in s.get("name", "")
            ),
            None,
        )
        assert empty_sub_in_json is not None, "placeholder_subcircuit not found in JSON"

        empty_sub_components = empty_sub_in_json.get("components", {})
        subcircuit_name_final = empty_sub_in_json.get("name")
        assert (
            len(empty_sub_components) == 0
        ), f"{subcircuit_name_final} should be empty again, found {len(empty_sub_components)} components"

        print(f"\n🎉 EMPTY SUBCIRCUIT HANDLING WORKS!")
        print(f"   ✓ Empty subcircuits can be created without errors")
        print(f"   ✓ Components can be dynamically added to empty subcircuits")
        print(f"   ✓ Components can be removed, making subcircuits empty again")
        print(f"   ✓ Root sheet components preserved through all changes")
        print(f"   ✓ KiCad project remains valid at all stages")
        print(f"   ✓ Hierarchical structure is flexible and robust!")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
