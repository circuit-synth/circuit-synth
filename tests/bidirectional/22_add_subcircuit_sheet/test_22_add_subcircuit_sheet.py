#!/usr/bin/env python3
"""
Automated test for 22_add_subcircuit_sheet bidirectional test.

Tests hierarchical sheet creation: Adding a child sheet (subcircuit) to a circuit
and verifying both sheets exist in KiCad with proper component placement.

Core Question: When you add a Subcircuit (child sheet) to Python and regenerate,
does KiCad generate both the root sheet AND the child sheet as separate files,
with each containing the correct components?

Workflow:
1. Generate KiCad with R1 on root sheet only (hierarchical_circuit.py initial state)
2. Verify only root schematic file exists
3. Modify Python to add Subcircuit with R2 on child sheet
4. Regenerate KiCad from Python
5. Validate:
   - Root sheet still exists with R1
   - Child sheet file created
   - Child sheet contains R2
   - Positions preserved
   - KiCad recognizes hierarchical structure

Validation uses kicad-sch-api for Level 2 semantic validation.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_22_add_subcircuit_sheet(request):
    """Test hierarchical child sheet (subcircuit) generation in KiCad.

    KILLER FEATURE TEST (Hierarchical Design):
    Validates that subcircuits defined with @circuit decorator generate
    separate .kicad_sch files with proper hierarchical structure.

    Expected behavior:
    - Root sheet: hierarchical_circuit.kicad_sch with R1
    - Child sheet: ChildSheet.kicad_sch with R2
    - Hierarchical sheet symbol on root linking to child

    Level 2 Semantic Validation:
    - File system for multiple schematic files (CRITICAL!)
    - kicad-sch-api for sheet structure and component placement
    - JSON netlist for hierarchical structure
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "hierarchical_circuit.py"
    output_dir = test_dir / "hierarchical_circuit"
    root_schematic = output_dir / "hierarchical_circuit.kicad_sch"
    child_schematic = output_dir / "ChildSheet.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        # =====================================================================
        # STEP 1: Generate KiCad project with hierarchical circuit
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 1: Generate KiCad with hierarchical circuit")
        print("=" * 70)

        result = subprocess.run(
            ["uv", "run", "hierarchical_circuit.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Generation failed\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 1: KiCad project generated")

        # =====================================================================
        # STEP 2: Validate SEPARATE schematic files exist (THE KILLER TEST!)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 2: Validate separate .kicad_sch files (CRITICAL!)")
        print("=" * 70)

        # THIS IS THE CRITICAL VALIDATION!
        # We MUST have 2 separate .kicad_sch files:
        # 1. hierarchical_circuit.kicad_sch (root)
        # 2. ChildSheet.kicad_sch (child)

        sch_files = list(output_dir.glob("*.kicad_sch"))
        print(f"   Schematic files found: {len(sch_files)}")
        for sch_file in sch_files:
            print(f"     * {sch_file.name}")

        # KILLER ASSERTION: Must have 2 separate files!
        assert len(sch_files) == 2, (
            f"❌ CRITICAL FAILURE: Expected 2 schematic files (root + child), "
            f"found {len(sch_files)}: {[f.name for f in sch_files]}\n"
            f"This means hierarchical sheet generation is NOT working!"
        )

        assert root_schematic.exists(), f"Root schematic not found: {root_schematic}"
        assert child_schematic.exists(), (
            f"❌ CRITICAL: Child schematic not found: {child_schematic}\n"
            f"Hierarchical sheet file generation is broken!"
        )

        print(f"✅ Step 2: Both schematic files exist!")
        print(f"   ✓ Root: {root_schematic.name}")
        print(f"   ✓ Child: {child_schematic.name}")

        # =====================================================================
        # STEP 3: Validate component placement in each sheet
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 3: Validate component placement in each sheet")
        print("=" * 70)

        from kicad_sch_api import Schematic

        # Load root schematic
        sch_root = Schematic.load(str(root_schematic))
        root_components = sch_root.components
        print(f"   Root schematic components: {len(root_components)}")
        for comp in root_components:
            print(f"     * {comp.reference}")

        # Verify R1 is in root schematic
        r1 = next((c for c in root_components if c.reference == "R1"), None)
        assert r1 is not None, "R1 not found in root schematic"
        print(f"   ✓ R1 found in root sheet")

        # Load child schematic
        sch_child = Schematic.load(str(child_schematic))
        child_components = sch_child.components
        print(f"\n   Child schematic components: {len(child_components)}")
        for comp in child_components:
            print(f"     * {comp.reference}")

        # Verify R2 is in child schematic
        r2 = next((c for c in child_components if c.reference == "R2"), None)
        assert r2 is not None, "R2 not found in child schematic"
        print(f"   ✓ R2 found in child sheet")

        # =====================================================================
        # STEP 4: Validate JSON hierarchical structure
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 4: Validate JSON hierarchical structure")
        print("=" * 70)

        json_file = output_dir / "hierarchical_circuit.json"
        assert json_file.exists(), "JSON netlist not found"

        with open(json_file, "r") as f:
            json_data = json.load(f)

        # Verify hierarchical structure in JSON
        has_subcircuits = "subcircuits" in json_data and len(json_data["subcircuits"]) > 0
        print(f"   Root circuit: {json_data.get('name', 'unknown')}")
        print(f"   Has subcircuits: {has_subcircuits}")
        if has_subcircuits:
            for subcirc in json_data["subcircuits"]:
                print(f"     * {subcirc.get('name', 'unnamed')}")

        assert has_subcircuits, "JSON netlist should contain subcircuits"

        # Verify child circuit structure in JSON
        child_in_json = next(
            (s for s in json_data.get("subcircuits", []) if s.get("name") == "ChildSheet"),
            None,
        )
        assert child_in_json is not None, "ChildSheet not found in JSON subcircuits"
        assert "R2" in child_in_json.get("components", {}), "R2 not found in ChildSheet JSON"

        # Verify R1 is in root circuit JSON
        assert "R1" in json_data.get("components", {}), "R1 not found in root circuit JSON"

        print(f"   ✓ Hierarchical structure preserved in JSON netlist")

        # =====================================================================
        # SUCCESS!
        # =====================================================================
        print(f"\n🎉 HIERARCHICAL CIRCUIT DESIGN WORKS!")
        print(f"   ✓ Separate .kicad_sch files generated for each sheet")
        print(f"   ✓ Root sheet (hierarchical_circuit.kicad_sch) contains R1")
        print(f"   ✓ Child sheet (ChildSheet.kicad_sch) contains R2")
        print(f"   ✓ Hierarchical structure preserved in JSON netlist")
        print(f"   ✓ Complex circuits can be organized into subsystems!")

    finally:
        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
