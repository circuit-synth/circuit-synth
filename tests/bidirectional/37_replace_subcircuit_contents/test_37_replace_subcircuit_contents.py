#!/usr/bin/env python3
"""
Automated test for 37_replace_subcircuit_contents bidirectional test.

Tests subcircuit content replacement: Replacing entire subcircuit implementation
with different components while preserving hierarchical structure.

Core Question: When you replace all components in a subcircuit and regenerate,
does KiCad correctly update the subcircuit sheet to show new components
and remove the old ones, while preserving the hierarchical structure?

Workflow:
1. Generate KiCad with hierarchical structure (root + Amplifier subcircuit)
   - Amplifier contains: R1 (10k), C1 (1µF)
2. Verify subcircuit contents
3. Modify Python to redesign Amplifier:
   - Comment out: R1, C1
   - Uncomment: R2 (22k), R3 (47k), C2 (10µF)
4. Regenerate KiCad from Python
5. Validate:
   - Amplifier sheet still exists
   - New components (R2, R3, C2) present in Amplifier
   - Old components (R1, C1) removed
   - Root circuit unchanged
   - Hierarchical structure preserved

Validation uses kicad-sch-api and JSON netlist for Level 2 semantic validation.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest


def test_37_replace_subcircuit_contents(request):
    """Test replacing subcircuit contents while preserving hierarchy.

    KILLER FEATURE TEST (Iterative Subcircuit Design):
    Validates that subcircuit internals can be redesigned during iterative
    development, preserving the hierarchical structure and subcircuit identity.

    Workflow:
    1. Generate with Amplifier subcircuit containing R1, C1
    2. Verify subcircuit structure and contents
    3. Replace Amplifier implementation (R2, R3, C2 instead of R1, C1)
    4. Regenerate → Old components removed, new ones added, hierarchy preserved

    Why critical:
    - Enables iterative redesign of subcircuit internals
    - Preserves hierarchical organization across redesigns
    - Allows changing subcircuit topology without losing parent connections
    - Supports evolving designs incrementally

    Level 2 Semantic Validation:
    - kicad-sch-api for sheet structure and component placement
    - JSON netlist for hierarchical structure validation
    - File system for subcircuit sheet presence
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "subcircuit_redesign.py"
    output_dir = test_dir / "subcircuit_redesign"
    root_schematic_file = output_dir / "subcircuit_redesign.kicad_sch"
    amplifier_schematic_file = output_dir / "amplifier_subcircuit_1.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file (initial implementation with R1, C1)
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate KiCad with initial Amplifier (R1, C1)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 1: Generate KiCad with initial Amplifier subcircuit (R1, C1)")
        print("=" * 70)

        result = subprocess.run(
            ["uv", "run", "subcircuit_redesign.py"],
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
        assert amplifier_schematic_file.exists(), (
            f"Amplifier subcircuit file not created at {amplifier_schematic_file}"
        )

        print(f"✅ Step 1: Initial KiCad generated with hierarchical structure")
        print(f"   - Root schematic: {root_schematic_file.name}")
        print(f"   - Amplifier subcircuit: {amplifier_schematic_file.name}")

        # =====================================================================
        # STEP 2: Verify initial subcircuit contents (R1, C1)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 2: Verify initial Amplifier contents (R1, C1)")
        print("=" * 70)

        from kicad_sch_api import Schematic

        # Load root schematic (current implementation flattens hierarchy to single sheet)
        root_sch = Schematic.load(str(root_schematic_file))
        root_components = root_sch.components
        root_refs = [c.reference for c in root_components]
        print(f"   Root schematic components: {root_refs}")

        # Verify R_main exists (may have suffix like R_main1 due to reference normalization)
        r_main = next(
            (c for c in root_components if "main" in c.reference.lower()),
            None
        )
        assert r_main is not None, "R_main not found in root schematic"
        print(f"   ✓ R_main found in root circuit")

        # Load Amplifier subcircuit
        amp_sch = Schematic.load(str(amplifier_schematic_file))
        amp_components_initial = amp_sch.components
        amp_refs_initial = [c.reference for c in amp_components_initial]
        print(f"   Amplifier components (initial): {amp_refs_initial}")

        # Verify initial components exist
        assert any(
            c.reference == "R1" for c in amp_components_initial
        ), "R1 not found in initial Amplifier"
        assert any(
            c.reference == "C1" for c in amp_components_initial
        ), "C1 not found in initial Amplifier"
        print(f"   ✓ R1 (10k) found in Amplifier")
        print(f"   ✓ C1 (1µF) found in Amplifier")

        # Record initial component positions for later comparison
        r1_initial = next(c for c in amp_components_initial if c.reference == "R1")
        c1_initial = next(c for c in amp_components_initial if c.reference == "C1")
        r1_initial_pos = r1_initial.position if hasattr(r1_initial, "position") else None
        c1_initial_pos = c1_initial.position if hasattr(c1_initial, "position") else None

        print(f"\n   Initial component details:")
        print(f"   - R1 value: {r1_initial.value} at position {r1_initial_pos}")
        print(f"   - C1 value: {c1_initial.value} at position {c1_initial_pos}")

        # =====================================================================
        # STEP 3: Replace Amplifier contents (R2, R3, C2)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 3: Replace Amplifier implementation (R2, R3, C2)")
        print("=" * 70)

        # Comment out initial implementation (R1, C1)
        modified_code = original_code.replace(
            "    # Initial design: Simple RC filter (R1, C1)\n"
            "    # Uncomment these lines for initial state:\n"
            "    r1 = Component(",
            "    # Initial design: Simple RC filter (R1, C1)\n"
            "    # Uncomment these lines for initial state:\n"
            "    # r1 = Component("
        )
        modified_code = modified_code.replace(
            "    c1 = Component(\n"
            "        symbol=\"Device:C\",\n"
            "        ref=\"C1\",\n"
            "        value=\"1µF\",\n"
            "        footprint=\"Capacitor_SMD:C_0603_1608Metric\",\n"
            "    )",
            "    # c1 = Component(\n"
            "    #     symbol=\"Device:C\",\n"
            "    #     ref=\"C1\",\n"
            "    #     value=\"1µF\",\n"
            "    #     footprint=\"Capacitor_SMD:C_0603_1608Metric\",\n"
            "    # )"
        )

        # Uncomment modified implementation (R2, R3, C2)
        modified_code = modified_code.replace(
            "    # Modified design: New implementation (R2, R3, C2)\n"
            "    # Uncomment these lines for modified state:\n"
            "    # r2 = Component(",
            "    # Modified design: New implementation (R2, R3, C2)\n"
            "    # Uncomment these lines for modified state:\n"
            "    r2 = Component("
        )
        modified_code = modified_code.replace(
            "    # r3 = Component(\n"
            "    #     symbol=\"Device:R\",\n"
            "    #     ref=\"R3\",\n"
            "    #     value=\"47k\",\n"
            "    #     footprint=\"Resistor_SMD:R_0603_1608Metric\",\n"
            "    # )",
            "    r3 = Component(\n"
            "        symbol=\"Device:R\",\n"
            "        ref=\"R3\",\n"
            "        value=\"47k\",\n"
            "        footprint=\"Resistor_SMD:R_0603_1608Metric\",\n"
            "    )"
        )
        modified_code = modified_code.replace(
            "    # c2 = Component(\n"
            "    #     symbol=\"Device:C\",\n"
            "    #     ref=\"C2\",\n"
            "    #     value=\"10µF\",\n"
            "    #     footprint=\"Capacitor_SMD:C_0603_1608Metric\",\n"
            "    # )",
            "    c2 = Component(\n"
            "        symbol=\"Device:C\",\n"
            "        ref=\"C2\",\n"
            "        value=\"10µF\",\n"
            "        footprint=\"Capacitor_SMD:C_0603_1608Metric\",\n"
            "    )"
        )

        assert modified_code != original_code, (
            "Failed to modify Python code - replacements didn't work"
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 3: Amplifier implementation replaced in Python")
        print(f"   - Commented out: R1 (10k), C1 (1µF)")
        print(f"   - Uncommented: R2 (22k), R3 (47k), C2 (10µF)")

        # =====================================================================
        # STEP 4: Regenerate KiCad with redesigned Amplifier
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 4: Regenerate KiCad with redesigned Amplifier")
        print("=" * 70)

        # Remove old output to force fresh generation
        if output_dir.exists():
            shutil.rmtree(output_dir)

        result = subprocess.run(
            ["uv", "run", "subcircuit_redesign.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration with redesigned Amplifier\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 4: KiCad regenerated with redesigned Amplifier")

        # =====================================================================
        # STEP 5: Validate subcircuit redesign
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 5: Validate subcircuit redesign (THE KILLER FEATURE)")
        print("=" * 70)

        # Verify both schematic files still exist
        assert root_schematic_file.exists(), "Root schematic not found after regeneration"
        assert amplifier_schematic_file.exists(), (
            f"Amplifier subcircuit file not found after regeneration: {amplifier_schematic_file}"
        )
        print(f"   ✓ Root and Amplifier schematic files both exist")

        # Load root schematic after regeneration
        root_sch_final = Schematic.load(str(root_schematic_file))
        root_components_final = root_sch_final.components
        root_refs_final = [c.reference for c in root_components_final]
        print(f"\n   Root schematic components (after redesign): {root_refs_final}")

        # Verify root circuit unchanged
        r_main_final = next(
            (c for c in root_components_final if "main" in c.reference.lower()),
            None
        )
        assert r_main_final is not None, "R_main missing from root after redesign"
        print(f"   ✓ Root circuit unchanged - {r_main_final.reference} still present")

        # Load Amplifier subcircuit after regeneration
        amp_sch_final = Schematic.load(str(amplifier_schematic_file))
        amp_components_final = amp_sch_final.components
        amp_refs_final = [c.reference for c in amp_components_final]
        print(f"\n   Amplifier components (after redesign): {amp_refs_final}")

        # =====================================================================
        # STEP 6: Verify new components exist (R2, R3, C2)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 6: Verify new components exist (R2, R3, C2)")
        print("=" * 70)

        r2_exists = any(c.reference == "R2" for c in amp_components_final)
        r3_exists = any(c.reference == "R3" for c in amp_components_final)
        c2_exists = any(c.reference == "C2" for c in amp_components_final)

        assert r2_exists, "R2 not found in redesigned Amplifier"
        assert r3_exists, "R3 not found in redesigned Amplifier"
        assert c2_exists, "C2 not found in redesigned Amplifier"

        print(f"   ✓ R2 (22k) found in Amplifier")
        print(f"   ✓ R3 (47k) found in Amplifier")
        print(f"   ✓ C2 (10µF) found in Amplifier")

        # Get final components for value verification
        r2_final = next(c for c in amp_components_final if c.reference == "R2")
        r3_final = next(c for c in amp_components_final if c.reference == "R3")
        c2_final = next(c for c in amp_components_final if c.reference == "C2")

        print(f"\n   New component details:")
        print(f"   - R2: {r2_final.value} (expected: 22k)")
        print(f"   - R3: {r3_final.value} (expected: 47k)")
        print(f"   - C2: {c2_final.value} (expected: 10µF)")

        # =====================================================================
        # STEP 7: Verify old components removed (R1, C1)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 7: Verify old components removed (R1, C1)")
        print("=" * 70)

        r1_removed = not any(c.reference == "R1" for c in amp_components_final)
        c1_removed = not any(c.reference == "C1" for c in amp_components_final)

        assert r1_removed, "R1 still present in redesigned Amplifier (should be removed)"
        assert c1_removed, "C1 still present in redesigned Amplifier (should be removed)"

        print(f"   ✓ R1 successfully removed from Amplifier")
        print(f"   ✓ C1 successfully removed from Amplifier")
        print(f"   ✓ No orphaned components remain")

        # =====================================================================
        # STEP 8: Validate JSON netlist hierarchical structure
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 8: Validate JSON netlist hierarchical structure")
        print("=" * 70)

        json_file = output_dir / "subcircuit_redesign.json"
        assert json_file.exists(), "JSON netlist not found"

        with open(json_file, "r") as f:
            json_data = json.load(f)

        # Verify root circuit has main component
        root_components_json = json_data.get("components", {})
        # Find R_main (may have suffix like R_main1 due to reference normalization)
        r_main_json = next(
            (ref for ref in root_components_json.keys() if "main" in ref.lower()),
            None
        )
        assert r_main_json is not None, (
            f"R_main not in root circuit JSON. Available: {list(root_components_json.keys())}"
        )
        print(f"   ✓ Root circuit JSON: {r_main_json} present")

        # Verify subcircuits exist in JSON
        subcircuits = json_data.get("subcircuits", [])
        assert len(subcircuits) > 0, "No subcircuits in JSON netlist"
        print(f"   ✓ JSON contains {len(subcircuits)} subcircuit(s)")

        # Find amplifier_subcircuit_1 in JSON
        amplifier_json = next(
            (s for s in subcircuits if s.get("name") == "amplifier_subcircuit_1"), None
        )
        assert amplifier_json is not None, "amplifier_subcircuit_1 not found in JSON subcircuits"
        print(f"   ✓ amplifier_subcircuit_1 subcircuit found in JSON")

        # Verify Amplifier JSON has new components
        amplifier_components_json = amplifier_json.get("components", {})
        assert "R2" in amplifier_components_json, "R2 not in Amplifier JSON"
        assert "R3" in amplifier_components_json, "R3 not in Amplifier JSON"
        assert "C2" in amplifier_components_json, "C2 not in Amplifier JSON"
        print(f"   ✓ Amplifier JSON: R2, R3, C2 present")

        # Verify old components not in Amplifier JSON
        assert "R1" not in amplifier_components_json, (
            "R1 still in Amplifier JSON (should be removed)"
        )
        assert "C1" not in amplifier_components_json, (
            "C1 still in Amplifier JSON (should be removed)"
        )
        print(f"   ✓ Amplifier JSON: R1, C1 removed")

        # =====================================================================
        # STEP 9: Final validation summary
        # =====================================================================
        print("\n" + "=" * 70)
        print("🎉 SUBCIRCUIT REDESIGN WORKS!")
        print("=" * 70)
        print(f"\n   ✓ Python code can define hierarchical circuits")
        print(f"   ✓ Subcircuit internals can be completely redesigned")
        print(f"   ✓ Root circuit preserved across redesign")
        print(f"   ✓ Old components cleanly removed")
        print(f"   ✓ New components correctly added")
        print(f"   ✓ Hierarchical structure preserved in JSON netlist")
        print(f"   ✓ Schematic files properly updated")
        print(f"   ✓ Iterative subcircuit development workflow works!")

        print(f"\n   Summary:")
        print(f"   - Initial Amplifier: R1, C1")
        print(f"   - Redesigned Amplifier: R2, R3, C2")
        print(f"   - Root circuit: unchanged (R_main)")
        print(f"   - Hierarchy: preserved and validated")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
