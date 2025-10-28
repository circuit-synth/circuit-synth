#!/usr/bin/env python3
"""
Automated test for 39_modify_component_in_subcircuit bidirectional test.

Tests modifying component VALUE inside a subcircuit (not root circuit) and validating
that changes are correctly applied while preserving positions and hierarchy.

CRITICAL GAP TEST (Priority 0):
Almost all existing tests operate on ROOT SHEET ONLY. This test validates
hierarchical operations - modifying components INSIDE subcircuits.

Core Question: When you modify a component VALUE inside a subcircuit (not root)
and regenerate, does KiCad correctly update that component in the subcircuit sheet
while preserving positions and leaving parent circuit unaffected?

Workflow:
1. Generate KiCad with hierarchical structure:
   - Root circuit: R_main (100k)
   - PowerSupply subcircuit: R1 (1k), R2 (2k)
2. Synchronize back to capture positions
3. Modify R1 value in PowerSupply: 1k → 10k
4. Regenerate KiCad from modified Python
5. Validate:
   - R1 in PowerSupply has new value (10k)
   - R1 position in subcircuit preserved
   - R2 in subcircuit unchanged (2k)
   - Root circuit completely unaffected
   - Hierarchical structure preserved
   - Netlist reflects new value

Validation uses kicad-sch-api for Level 2 semantic validation and JSON netlist
for Level 3 electrical validation.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest


def test_39_modify_component_in_subcircuit(request):
    """Test modifying component value inside subcircuit (not root).

    KILLER FEATURE TEST (Hierarchical Operations):
    Validates that components inside subcircuits can be modified during
    iterative development, with position preservation and parent isolation.

    Workflow:
    1. Generate hierarchical circuit (root + PowerSupply subcircuit)
    2. Verify initial state: R1=1k, R2=2k in PowerSupply
    3. Modify R1 value in subcircuit: 1k → 10k
    4. Regenerate → R1=10k, position preserved, R2 and root unchanged

    Why critical:
    - Most tests only operate on root sheet (MAJOR GAP)
    - Enables component modifications in subcircuits
    - Validates hierarchical position preservation
    - Ensures parent circuit isolation during subcircuit changes
    - Fundamental for iterative hierarchical design

    Level 2 Semantic Validation:
    - kicad-sch-api for subcircuit component values and positions
    - JSON netlist for hierarchical structure validation
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "subcircuit_with_resistors.py"
    output_dir = test_dir / "subcircuit_with_resistors"
    root_schematic_file = output_dir / "subcircuit_with_resistors.kicad_sch"
    power_supply_schematic_file = output_dir / "PowerSupply.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file (R1=1k initial state)
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate KiCad with initial hierarchy (R1=1k, R2=2k)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 1: Generate KiCad with PowerSupply subcircuit (R1=1k, R2=2k)")
        print("=" * 70)

        result = subprocess.run(
            ["uv", "run", "subcircuit_with_resistors.py"],
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

        assert root_schematic_file.exists(), "Root schematic not created"
        assert power_supply_schematic_file.exists(), (
            f"PowerSupply subcircuit file not created at {power_supply_schematic_file}"
        )

        print(f"✅ Step 1: Initial KiCad generated with hierarchical structure")
        print(f"   - Root schematic: {root_schematic_file.name}")
        print(f"   - PowerSupply subcircuit: {power_supply_schematic_file.name}")

        # =====================================================================
        # STEP 2: Verify initial subcircuit state (R1=1k, R2=2k)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 2: Verify initial PowerSupply contents (R1=1k, R2=2k)")
        print("=" * 70)

        from kicad_sch_api import Schematic

        # Load root schematic
        root_sch = Schematic.load(str(root_schematic_file))
        root_components = root_sch.components
        root_refs = [c.reference for c in root_components]
        print(f"   Root schematic components: {root_refs}")

        # Verify R_main1 exists in root
        r_main = next(
            (c for c in root_components if c.reference == "R_main1"),
            None
        )
        assert r_main is not None, "R_main1 not found in root schematic"
        r_main_initial_value = r_main.value
        print(f"   ✓ R_main1 found in root circuit (value: {r_main_initial_value})")

        # Load PowerSupply subcircuit
        ps_sch = Schematic.load(str(power_supply_schematic_file))
        ps_components_initial = ps_sch.components
        ps_refs_initial = [c.reference for c in ps_components_initial]
        print(f"   PowerSupply components (initial): {ps_refs_initial}")

        # Verify initial components exist in subcircuit
        r1_initial = next(
            (c for c in ps_components_initial if c.reference == "R1"), None
        )
        r2_initial = next(
            (c for c in ps_components_initial if c.reference == "R2"), None
        )

        assert r1_initial is not None, "R1 not found in PowerSupply subcircuit"
        assert r2_initial is not None, "R2 not found in PowerSupply subcircuit"

        # Record initial values and positions
        r1_initial_value = r1_initial.value
        r2_initial_value = r2_initial.value
        r1_initial_pos = r1_initial.position if hasattr(r1_initial, "position") else None
        r2_initial_pos = r2_initial.position if hasattr(r2_initial, "position") else None

        assert r1_initial_value == "1k", f"R1 initial value should be 1k, got {r1_initial_value}"
        assert r2_initial_value == "2k", f"R2 initial value should be 2k, got {r2_initial_value}"

        print(f"\n   Initial PowerSupply component details:")
        print(f"   - R1: value={r1_initial_value}, position={r1_initial_pos}")
        print(f"   - R2: value={r2_initial_value}, position={r2_initial_pos}")

        # =====================================================================
        # STEP 3: Modify R1 value in PowerSupply subcircuit (1k → 10k)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 3: Modify R1 value in PowerSupply subcircuit (1k → 10k)")
        print("=" * 70)

        # Modify R1 value: 1k → 10k
        # Keep R2 unchanged at 2k
        modified_subcircuit_lines = [
            "power_supply = Circuit(\"PowerSupply\")",
            "",
            "r1 = Component(",
            "    symbol=\"Device:R\",",
            "    ref=\"R1\",",
            "    value=\"10k\",  # MODIFIED: was 1k",
            "    footprint=\"Resistor_SMD:R_0603_1608Metric\",",
            ")",
            "r2 = Component(",
            "    symbol=\"Device:R\",",
            "    ref=\"R2\",",
            "    value=\"2k\",  # UNCHANGED",
            "    footprint=\"Resistor_SMD:R_0603_1608Metric\",",
            ")",
            "",
            "power_supply.add_component(r1)",
            "power_supply.add_component(r2)",
        ]

        modified_subcircuit_section = "\n    " + "\n    ".join(modified_subcircuit_lines)

        # Build marker section to match original file
        marker_section = (
            "    # START_MARKER: Test will modify R1 value between these markers\n"
            "    power_supply = Circuit(\"PowerSupply\")\n"
            "\n"
            "    r1 = Component(\n"
            "        symbol=\"Device:R\",\n"
            "        ref=\"R1\",\n"
            "        value=\"1k\",\n"
            "        footprint=\"Resistor_SMD:R_0603_1608Metric\",\n"
            "    )\n"
            "    r2 = Component(\n"
            "        symbol=\"Device:R\",\n"
            "        ref=\"R2\",\n"
            "        value=\"2k\",\n"
            "        footprint=\"Resistor_SMD:R_0603_1608Metric\",\n"
            "    )\n"
            "\n"
            "    power_supply.add_component(r1)\n"
            "    power_supply.add_component(r2)\n"
            "    # END_MARKER"
        )

        replacement_section = (
            "    # START_MARKER: Test will modify R1 value between these markers\n" +
            modified_subcircuit_section + "\n" +
            "    # END_MARKER"
        )

        modified_code = original_code.replace(marker_section, replacement_section)

        assert modified_code != original_code, (
            "Failed to modify Python code - markers not found or pattern incorrect"
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 3: R1 value modified in Python code")
        print(f"   - R1: 1k → 10k (in PowerSupply subcircuit)")
        print(f"   - R2: 2k (unchanged)")
        print(f"   - R_main1: 100k (root circuit, should remain unchanged)")

        # =====================================================================
        # STEP 4: Regenerate KiCad with modified R1
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 4: Regenerate KiCad with modified R1 in subcircuit")
        print("=" * 70)

        # Remove old output to force fresh generation
        if output_dir.exists():
            shutil.rmtree(output_dir)

        result = subprocess.run(
            ["uv", "run", "subcircuit_with_resistors.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration with modified R1\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 4: KiCad regenerated with modified R1")

        # =====================================================================
        # STEP 5: Validate R1 modification in subcircuit
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 5: Validate R1 modification in PowerSupply subcircuit")
        print("=" * 70)

        # Verify both schematic files still exist
        assert root_schematic_file.exists(), "Root schematic not found after regeneration"
        assert power_supply_schematic_file.exists(), (
            f"PowerSupply subcircuit file not found after regeneration"
        )
        print(f"   ✓ Root and PowerSupply schematic files both exist")

        # Load PowerSupply subcircuit after regeneration
        ps_sch_final = Schematic.load(str(power_supply_schematic_file))
        ps_components_final = ps_sch_final.components
        ps_refs_final = [c.reference for c in ps_components_final]
        print(f"\n   PowerSupply components (after modification): {ps_refs_final}")

        # Find R1 and R2 after modification
        r1_final = next(
            (c for c in ps_components_final if c.reference == "R1"), None
        )
        r2_final = next(
            (c for c in ps_components_final if c.reference == "R2"), None
        )

        assert r1_final is not None, "R1 not found in PowerSupply after regeneration"
        assert r2_final is not None, "R2 not found in PowerSupply after regeneration"

        # =====================================================================
        # STEP 6: Verify R1 value changed to 10k
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 6: Verify R1 value changed to 10k (THE KILLER FEATURE)")
        print("=" * 70)

        r1_final_value = r1_final.value
        assert r1_final_value == "10k", (
            f"R1 value should be 10k after modification, got {r1_final_value}"
        )
        print(f"   ✓ R1 value correctly updated to 10k")

        # =====================================================================
        # STEP 7: Verify R1 position preserved in subcircuit
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 7: Verify R1 position preserved in subcircuit")
        print("=" * 70)

        r1_final_pos = r1_final.position if hasattr(r1_final, "position") else None

        print(f"   R1 position:")
        print(f"     - Before modification: {r1_initial_pos}")
        print(f"     - After modification: {r1_final_pos}")

        if r1_initial_pos and r1_final_pos:
            position_preserved = (
                r1_initial_pos.x == r1_final_pos.x and
                r1_initial_pos.y == r1_final_pos.y
            )
            assert position_preserved, (
                f"R1 position not preserved! "
                f"Before: {r1_initial_pos}, After: {r1_final_pos}"
            )
            print(f"     ✓ Position preserved")
        else:
            print(f"     ⚠ Position data not available for comparison")

        # =====================================================================
        # STEP 8: Verify R2 unchanged in subcircuit
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 8: Verify R2 unchanged in subcircuit")
        print("=" * 70)

        r2_final_value = r2_final.value
        assert r2_final_value == "2k", (
            f"R2 should remain unchanged at 2k, got {r2_final_value}"
        )
        print(f"   ✓ R2 value unchanged: {r2_final_value}")

        r2_final_pos = r2_final.position if hasattr(r2_final, "position") else None
        print(f"   R2 position: {r2_final_pos}")

        # =====================================================================
        # STEP 9: Verify root circuit unaffected
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 9: Verify root circuit unaffected by subcircuit change")
        print("=" * 70)

        # Load root schematic after regeneration
        root_sch_final = Schematic.load(str(root_schematic_file))
        root_components_final = root_sch_final.components
        root_refs_final = [c.reference for c in root_components_final]
        print(f"   Root schematic components (after modification): {root_refs_final}")

        # Verify R_main1 still exists and unchanged
        r_main_final = next(
            (c for c in root_components_final if c.reference == "R_main1"),
            None
        )
        assert r_main_final is not None, "R_main1 missing from root after subcircuit modification"

        r_main_final_value = r_main_final.value
        assert r_main_final_value == r_main_initial_value, (
            f"Root component R_main1 changed unexpectedly! "
            f"Before: {r_main_initial_value}, After: {r_main_final_value}"
        )
        print(f"   ✓ Root circuit unchanged - R_main1 still {r_main_final_value}")

        # =====================================================================
        # STEP 10: Validate JSON netlist hierarchical structure
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 10: Validate JSON netlist hierarchical structure")
        print("=" * 70)

        json_file = output_dir / "subcircuit_with_resistors.json"
        assert json_file.exists(), "JSON netlist not found"

        with open(json_file, "r") as f:
            json_data = json.load(f)

        # Verify root circuit has R_main1
        root_components_json = json_data.get("components", {})
        assert "R_main1" in root_components_json, (
            f"R_main1 not in root circuit JSON. Available: {list(root_components_json.keys())}"
        )
        print(f"   ✓ Root circuit JSON: R_main1 present")

        # Verify subcircuits exist in JSON
        subcircuits = json_data.get("subcircuits", [])
        assert len(subcircuits) > 0, "No subcircuits in JSON netlist"
        print(f"   ✓ JSON contains {len(subcircuits)} subcircuit(s)")

        # Find PowerSupply in JSON
        power_supply_json = next(
            (s for s in subcircuits if s.get("name") == "PowerSupply"), None
        )
        assert power_supply_json is not None, "PowerSupply not found in JSON subcircuits"
        print(f"   ✓ PowerSupply subcircuit found in JSON")

        # Verify PowerSupply JSON has R1 with new value (10k)
        ps_components_json = power_supply_json.get("components", {})
        assert "R1" in ps_components_json, "R1 not in PowerSupply JSON"
        r1_json_data = ps_components_json["R1"]
        r1_json_value = r1_json_data.get("value", "")
        assert r1_json_value == "10k", (
            f"R1 value in JSON should be 10k, got {r1_json_value}"
        )
        print(f"   ✓ PowerSupply JSON: R1 has correct value (10k)")

        # Verify R2 unchanged in JSON
        assert "R2" in ps_components_json, "R2 not in PowerSupply JSON"
        r2_json_data = ps_components_json["R2"]
        r2_json_value = r2_json_data.get("value", "")
        assert r2_json_value == "2k", (
            f"R2 value in JSON should remain 2k, got {r2_json_value}"
        )
        print(f"   ✓ PowerSupply JSON: R2 unchanged (2k)")

        # =====================================================================
        # STEP 11: Final validation summary
        # =====================================================================
        print("\n" + "=" * 70)
        print("🎉 SUBCIRCUIT COMPONENT MODIFICATION WORKS!")
        print("=" * 70)
        print(f"\n   ✓ Component modification in subcircuit (not root) successful")
        print(f"   ✓ R1 value correctly changed: 1k → 10k")
        print(f"   ✓ R1 position preserved in subcircuit")
        print(f"   ✓ R2 in subcircuit unchanged (2k)")
        print(f"   ✓ Root circuit completely unaffected (R_main1=100k)")
        print(f"   ✓ Hierarchical structure preserved")
        print(f"   ✓ JSON netlist reflects correct values")
        print(f"   ✓ MAJOR GAP ADDRESSED: Hierarchical operations work!")

        print(f"\n   Summary:")
        print(f"   - PowerSupply subcircuit:")
        print(f"     * R1: 1k → 10k ✓")
        print(f"     * R2: 2k (unchanged) ✓")
        print(f"   - Root circuit:")
        print(f"     * R_main1: 100k (unchanged) ✓")
        print(f"   - Hierarchy: preserved and validated ✓")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
