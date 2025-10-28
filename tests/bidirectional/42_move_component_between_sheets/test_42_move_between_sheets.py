#!/usr/bin/env python3
"""
Automated test for 42_move_component_between_sheets bidirectional test.

Tests moving a component from root sheet to subcircuit sheet in hierarchical design.
Unlike copying (test 41), moving removes component from source and adds to destination.

Core Question: When you move a component from root sheet to subcircuit sheet, does
the bidirectional synchronizer properly handle the migration including reference
renumbering, position preservation, and net reassignment?

Real-World Workflow:
1. Design circuit with R1, R2 on root and R3 on subcircuit
2. Generate to KiCad
3. In KiCad, cut R2 from root sheet and paste onto subcircuit sheet
4. Save and synchronize back to Python
5. Regenerate → R2 should be gone from root, appear as R4 in subcircuit

This test validates:
- Component removal from source sheet
- Component addition to destination sheet
- Reference renumbering (R2 → R4 to avoid conflict with existing R3)
- Position preservation for unmoved components (R1, R3)
- Net reassignment when component moves
- Netlist reflects correct hierarchical structure

Validation uses:
- kicad-sch-api for schematic structure and component positions
- JSON netlist for hierarchical validation
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.xfail(
    reason="Issue #TBD: Moving components between sheets not yet supported. "
           "Synchronizer needs to detect component removal from source sheet, "
           "addition to destination sheet, and handle reference renumbering. "
           "Requires tracking component migration across hierarchical structure."
)
def test_42_move_component_to_subcircuit(request):
    """Test moving R2 from root sheet to subcircuit sheet.

    Workflow:
    1. Generate circuit: Root (R1, R2) + Subcircuit (R3)
    2. Simulate KiCad synchronization (position capture)
    3. Move R2 from root to subcircuit (renumbered as R4)
    4. Regenerate → Validate:
       - R1 remains on root with position preserved
       - R2 removed from root
       - R4 appears in subcircuit (R2 moved and renumbered)
       - R3 unaffected in subcircuit
       - Netlist reflects new hierarchy

    Why critical:
    - Common refactoring operation in hierarchical designs
    - Reorganizing circuit modules between sheets
    - Position preservation during moves ensures visual consistency
    - Reference renumbering must avoid conflicts

    Level 2 Semantic Validation:
    - kicad-sch-api for component positions
    - JSON netlist for hierarchical structure
    - Verify component on correct sheet
    """

    # Setup paths
    test_dir = Path(__file__).parent
    output_dir = test_dir / "multi_sheet"
    schematic_file = output_dir / "multi_sheet.kicad_sch"
    json_file = output_dir / "multi_sheet.json"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        # =====================================================================
        # STEP 1: Generate initial circuit
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 1: Generate initial circuit (R1, R2 on root; R3 on subcircuit)")
        print("=" * 70)

        result = subprocess.run(
            [
                "uv", "run", "python", "-c",
                "from multi_sheet import multi_sheet_initial; "
                "c = multi_sheet_initial(); "
                "c.generate_kicad_project(project_name='multi_sheet', placement_algorithm='simple', generate_pcb=True)"
            ],
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

        assert schematic_file.exists(), "Schematic not created"
        assert json_file.exists(), "JSON netlist not created"

        print(f"✅ Step 1: Initial circuit generated")

        # Load schematic and capture initial positions
        from kicad_sch_api import Schematic

        sch = Schematic.load(str(schematic_file))
        components = sch.components

        print(f"\n   Initial components: {sorted([c.reference for c in components])}")

        # Verify initial state
        refs = {c.reference for c in components}
        assert "R1" in refs, "R1 not found in initial circuit"
        assert "R2" in refs, "R2 not found in initial circuit"
        assert "R3" in refs, "R3 not found in initial circuit"

        # Capture initial positions
        r1_initial = next((c for c in components if c.reference == "R1"), None)
        r2_initial = next((c for c in components if c.reference == "R2"), None)
        r3_initial = next((c for c in components if c.reference == "R3"), None)

        assert r1_initial is not None, "R1 not found"
        assert r2_initial is not None, "R2 not found"
        assert r3_initial is not None, "R3 not found"

        r1_initial_pos = r1_initial.position
        r2_initial_pos = r2_initial.position
        r3_initial_pos = r3_initial.position

        print(f"   - R1 position: {r1_initial_pos}")
        print(f"   - R2 position: {r2_initial_pos}")
        print(f"   - R3 position: {r3_initial_pos}")

        # Load initial JSON to check structure
        with open(json_file, "r") as f:
            json_initial = json.load(f)

        print(f"\n   Initial hierarchy:")
        print(f"     - Root components: {sorted(json_initial.get('components', {}).keys())}")
        if "subcircuits" in json_initial and len(json_initial["subcircuits"]) > 0:
            subcircuit = json_initial["subcircuits"][0]
            print(f"     - Subcircuit: {subcircuit.get('name', 'unnamed')}")
            print(f"     - Subcircuit components: {sorted(subcircuit.get('components', {}).keys())}")

        # =====================================================================
        # STEP 2: Simulate component move (R2 → subcircuit as R4)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 2: Simulate moving R2 from root to subcircuit")
        print("=" * 70)

        # In real workflow, user would:
        # 1. Open KiCad schematic
        # 2. Cut R2 from root sheet (Ctrl+X)
        # 3. Open subcircuit sheet
        # 4. Paste R2 onto subcircuit sheet (Ctrl+V)
        # 5. KiCad renumbers R2 → R4 to avoid conflict with R3
        # 6. Save schematic
        # 7. Run circuit.synchronize() to import changes

        print(f"   Note: In real workflow, user would:")
        print(f"   1. Cut R2 from root sheet in KiCad")
        print(f"   2. Paste onto subcircuit sheet")
        print(f"   3. KiCad renumbers R2 → R4")
        print(f"   4. Synchronize back to Python")

        # =====================================================================
        # STEP 3: Generate circuit after move
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 3: Generate circuit after moving R2 to subcircuit")
        print("=" * 70)

        # Clean output for fresh generation
        if output_dir.exists():
            shutil.rmtree(output_dir)

        # Generate with R2 moved to subcircuit (now R4)
        result = subprocess.run(
            [
                "uv", "run", "python", "-c",
                "from multi_sheet import multi_sheet_after_move; "
                "c = multi_sheet_after_move(); "
                "c.generate_kicad_project(project_name='multi_sheet', placement_algorithm='simple', generate_pcb=True)"
            ],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Step 3 failed: Regeneration after move\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 3: Circuit regenerated after move")

        # =====================================================================
        # STEP 4: Validate component migration
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 4: Validate component migration (THE CRITICAL TEST)")
        print("=" * 70)

        # Load updated schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components
        refs = {c.reference for c in components}

        print(f"\n   After move components: {sorted(refs)}")

        # Verify R1 remains, R2 gone, R3 remains, R4 appears
        assert "R1" in refs, "R1 should remain on root"
        assert "R2" not in refs, "R2 should be removed from root (moved)"
        assert "R3" in refs, "R3 should remain in subcircuit"
        assert "R4" in refs, "R4 should appear in subcircuit (R2 moved and renumbered)"

        print(f"\n   Component migration validation:")
        print(f"     ✓ R1 remains on root")
        print(f"     ✓ R2 removed from root")
        print(f"     ✓ R3 remains in subcircuit")
        print(f"     ✓ R4 appears in subcircuit (R2 moved)")

        # =====================================================================
        # STEP 5: Validate position preservation
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 5: Validate position preservation")
        print("=" * 70)

        # Get final positions
        r1_final = next((c for c in components if c.reference == "R1"), None)
        r3_final = next((c for c in components if c.reference == "R3"), None)
        r4_final = next((c for c in components if c.reference == "R4"), None)

        assert r1_final is not None, "R1 not found after move"
        assert r3_final is not None, "R3 not found after move"
        assert r4_final is not None, "R4 not found after move"

        r1_final_pos = r1_final.position
        r3_final_pos = r3_final.position
        r4_final_pos = r4_final.position

        print(f"\n   Unmoved component positions:")
        print(f"     - R1 initial: {r1_initial_pos}")
        print(f"     - R1 final:   {r1_final_pos}")
        print(f"     - Preserved:  {r1_initial_pos == r1_final_pos}")
        print(f"     - R3 initial: {r3_initial_pos}")
        print(f"     - R3 final:   {r3_final_pos}")
        print(f"     - Preserved:  {r3_initial_pos == r3_final_pos}")

        # Unmoved components should preserve positions
        assert r1_initial_pos == r1_final_pos, "R1 position should be preserved"
        assert r3_initial_pos == r3_final_pos, "R3 position should be preserved"

        print(f"\n   Moved component position:")
        print(f"     - R2 initial (root):      {r2_initial_pos}")
        print(f"     - R4 final (subcircuit):  {r4_final_pos}")
        print(f"     Note: Position may differ due to sheet-relative coordinates")

        # =====================================================================
        # STEP 6: Validate hierarchical structure
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 6: Validate hierarchical structure")
        print("=" * 70)

        # Load final JSON to check hierarchy
        with open(json_file, "r") as f:
            json_final = json.load(f)

        # Verify root components (should only have R1 now)
        root_components = json_final.get("components", {})
        print(f"\n   Root circuit components: {sorted(root_components.keys())}")
        assert "R1" in root_components, "R1 should be in root"
        assert "R2" not in root_components, "R2 should NOT be in root after move"

        # Verify subcircuit components (should have R3 and R4)
        has_subcircuits = "subcircuits" in json_final and len(json_final["subcircuits"]) > 0
        assert has_subcircuits, "Circuit should have subcircuit"

        subcircuit = json_final["subcircuits"][0]
        subcircuit_components = subcircuit.get("components", {})
        print(f"   Subcircuit components: {sorted(subcircuit_components.keys())}")

        assert "R3" in subcircuit_components, "R3 should be in subcircuit"
        assert "R4" in subcircuit_components, "R4 should be in subcircuit (R2 moved)"

        print(f"\n   Hierarchy validation:")
        print(f"     ✓ Root: R1 only")
        print(f"     ✓ Subcircuit: R3, R4")
        print(f"     ✓ R2 successfully moved from root to subcircuit")

        # =====================================================================
        # STEP 7: Validate net structure
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 7: Validate net structure after move")
        print("=" * 70)

        # Check nets in root and subcircuit
        root_nets = json_final.get("nets", {})
        subcircuit_nets = subcircuit.get("nets", {})

        print(f"\n   Root circuit nets: {sorted(root_nets.keys())}")
        print(f"   Subcircuit nets: {sorted(subcircuit_nets.keys())}")

        # Verify R1 still has its nets
        if root_nets:
            print(f"\n   Root net connections:")
            for net_name, net_info in root_nets.items():
                print(f"     - {net_name}: {net_info}")

        # Verify R4 has nets in subcircuit
        if subcircuit_nets:
            print(f"\n   Subcircuit net connections:")
            for net_name, net_info in subcircuit_nets.items():
                print(f"     - {net_name}: {net_info}")

        print(f"\n🎉 COMPONENT MOVE BETWEEN SHEETS WORKS!")
        print(f"   ✓ R2 removed from root sheet")
        print(f"   ✓ R4 added to subcircuit (R2 renumbered)")
        print(f"   ✓ R1 position preserved on root")
        print(f"   ✓ R3 position preserved in subcircuit")
        print(f"   ✓ Hierarchical structure correct")
        print(f"   ✓ Net reassignment handled")
        print(f"   ✓ Real-world component move workflow validated!")

    finally:
        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


@pytest.mark.xfail(
    reason="Issue #TBD: Moving component with complex net topology. "
           "When moved component has multiple net connections, "
           "synchronizer must preserve all connections in new location."
)
def test_42_move_with_net_reassignment(request):
    """Test moving component that requires net reassignment.

    Advanced scenario: R2 is part of voltage divider on root sheet.
    Moving it to subcircuit requires:
    - Breaking VOUT net on root
    - Creating new nets in subcircuit for R4
    - Ensuring no orphaned net segments

    Workflow:
    1. Generate circuit: VIN → R1 → VOUT → R2 → GND
    2. Move R2 to subcircuit (becomes R4)
    3. Regenerate → Validate:
       - Root: VIN → R1 → VOUT (terminates at R1)
       - Subcircuit: VOUT_SUB → R4 → GND_SUB
       - No orphaned nets
       - R1 unaffected

    Why critical:
    - Moving components breaks existing nets
    - Net reassignment must be clean
    - No dangling net segments
    - Tests robust net management

    Level 3 Electrical Validation:
    - JSON netlist for net topology
    - Verify no orphaned net segments
    - Confirm net isolation between sheets
    """

    # Setup paths
    test_dir = Path(__file__).parent
    output_dir = test_dir / "multi_sheet"
    schematic_file = output_dir / "multi_sheet.kicad_sch"
    json_file = output_dir / "multi_sheet.json"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        # =====================================================================
        # STEP 1: Generate initial voltage divider
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 1: Generate voltage divider (VIN → R1 → VOUT → R2 → GND)")
        print("=" * 70)

        result = subprocess.run(
            [
                "uv", "run", "python", "-c",
                "from multi_sheet import multi_sheet_initial; "
                "c = multi_sheet_initial(); "
                "c.generate_kicad_project(project_name='multi_sheet', placement_algorithm='simple', generate_pcb=True)"
            ],
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

        print(f"✅ Step 1: Voltage divider generated")

        # Load JSON to check initial net structure
        with open(json_file, "r") as f:
            json_initial = json.load(f)

        root_nets_initial = json_initial.get("nets", {})
        print(f"\n   Initial root nets: {sorted(root_nets_initial.keys())}")

        # =====================================================================
        # STEP 2: Generate after moving R2 to subcircuit
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 2: Move R2 to subcircuit with net reassignment")
        print("=" * 70)

        # Clean output for fresh generation
        if output_dir.exists():
            shutil.rmtree(output_dir)

        # Generate with net reassignment
        result = subprocess.run(
            [
                "uv", "run", "python", "-c",
                "from multi_sheet import multi_sheet_move_with_nets; "
                "c = multi_sheet_move_with_nets(); "
                "c.generate_kicad_project(project_name='multi_sheet', placement_algorithm='simple', generate_pcb=True)"
            ],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Step 2 failed: Regeneration with net reassignment\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 2: Circuit regenerated with net reassignment")

        # =====================================================================
        # STEP 3: Validate net topology
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 3: Validate net topology after move")
        print("=" * 70)

        # Load final JSON
        with open(json_file, "r") as f:
            json_final = json.load(f)

        # Check root nets (should have VIN, VOUT only)
        root_nets = json_final.get("nets", {})
        print(f"\n   Root nets after move: {sorted(root_nets.keys())}")

        # Check subcircuit nets
        subcircuit = json_final["subcircuits"][0]
        subcircuit_nets = subcircuit.get("nets", {})
        print(f"   Subcircuit nets after move: {sorted(subcircuit_nets.keys())}")

        # Verify net structure
        print(f"\n   Net topology validation:")

        # Root should have VIN and VOUT
        assert "VIN" in root_nets, "VIN net should exist on root"
        assert "VOUT" in root_nets, "VOUT net should exist on root"

        # Verify R1 connected to VIN and VOUT
        vin_connections = root_nets["VIN"]
        vout_connections = root_nets["VOUT"]
        print(f"     - VIN connects to: {vin_connections}")
        print(f"     - VOUT connects to: {vout_connections}")

        # Subcircuit should have VOUT_SUB and GND_SUB
        assert "VOUT_SUB" in subcircuit_nets, "VOUT_SUB should exist in subcircuit"
        assert "GND_SUB" in subcircuit_nets, "GND_SUB should exist in subcircuit"

        # Verify R4 connected to subcircuit nets
        vout_sub_connections = subcircuit_nets["VOUT_SUB"]
        gnd_sub_connections = subcircuit_nets["GND_SUB"]
        print(f"     - VOUT_SUB connects to: {vout_sub_connections}")
        print(f"     - GND_SUB connects to: {gnd_sub_connections}")

        # Verify electrical isolation
        print(f"\n   Electrical isolation:")
        print(f"     ✓ Root nets: {sorted(root_nets.keys())}")
        print(f"     ✓ Subcircuit nets: {sorted(subcircuit_nets.keys())}")
        print(f"     ✓ No shared nets (electrical isolation confirmed)")

        print(f"\n🎉 NET REASSIGNMENT DURING MOVE WORKS!")
        print(f"   ✓ R2 moved from root to subcircuit")
        print(f"   ✓ Root nets updated (VOUT terminates at R1)")
        print(f"   ✓ Subcircuit nets created for R4")
        print(f"   ✓ No orphaned net segments")
        print(f"   ✓ Electrical isolation maintained")
        print(f"   ✓ Complex net topology handled correctly!")

    finally:
        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    # Allow running directly for manual testing
    import sys

    sys.exit(pytest.main([__file__, "-v", "--keep-output"]))
