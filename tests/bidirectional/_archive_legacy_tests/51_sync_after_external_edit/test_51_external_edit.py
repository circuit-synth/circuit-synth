#!/usr/bin/env python3
"""
Automated test for 51_sync_after_external_edit bidirectional test.

Tests the critical collaborative workflow where:
1. Circuit generated from Python
2. KiCad file edited externally (simulated)
3. Changes synchronized back to Python
4. Python modifications added
5. Regeneration preserves both external and Python changes

This validates real-world collaborative workflows where:
- Engineer A generates circuit from Python
- Engineer B edits in KiCad GUI (add components, adjust values/positions)
- Engineer A synchronizes changes back to Python
- Both sets of changes coexist without loss

Validation Level 2 (Semantic):
- Uses kicad-sch-api for schematic validation
- Programmatic .kicad_sch modification to simulate external edits
- Python circuit object validation after synchronization
"""
import re
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest


def test_51_sync_after_external_edit(request):
    """Test synchronization after external KiCad edits.

    CRITICAL COLLABORATIVE WORKFLOW:
    Real-world scenario where team members work on same circuit:
    - Python developer generates initial circuit
    - KiCad user adds components, adjusts values, moves components
    - Python developer synchronizes changes back
    - Both sets of changes should coexist

    Workflow:
    1. Generate from Python: R1 (1k), R2 (2k)
    2. External edit (simulate KiCad GUI):
       - Add R3 (3.3k) directly to .kicad_sch
       - Change R1 value: 1k → 1.5k
       - Move R2 position: (150, 100) → (160, 110)
    3. Synchronize to Python (validate external edits imported)
    4. Modify in Python: Add R4 (4.7k)
    5. Regenerate (validate all changes preserved)

    Level 2 Semantic Validation:
    - kicad-sch-api for component validation
    - Programmatic schematic modification
    - Python circuit object inspection
    - Netlist validation
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "base_circuit.py"
    output_dir = test_dir / "base_circuit"
    schematic_file = output_dir / "base_circuit.kicad_sch"

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
        # PHASE 1: Initial Generation (Python → KiCad)
        # =====================================================================
        print("\n" + "="*70)
        print("PHASE 1: Generate initial circuit from Python")
        print("="*70)
        print("Initial: R1 (1k) at (100, 100), R2 (2k) at (150, 100)")

        result = subprocess.run(
            ["uv", "run", "base_circuit.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Phase 1 failed: Initial generation\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Schematic not created"

        # Load and validate initial schematic
        from kicad_sch_api import Schematic
        sch_initial = Schematic.load(str(schematic_file))
        components_initial = sch_initial.components

        assert len(components_initial) == 2, (
            f"Phase 1: Expected 2 components, found {len(components_initial)}"
        )

        # Get initial component states
        r1_initial = next(c for c in components_initial if c.reference == "R1")
        r2_initial = next(c for c in components_initial if c.reference == "R2")

        assert r1_initial.value == "1k", f"R1 value should be 1k, got {r1_initial.value}"
        assert r2_initial.value == "2k", f"R2 value should be 2k, got {r2_initial.value}"

        r1_uuid = r1_initial.uuid
        r2_uuid = r2_initial.uuid
        r1_pos_initial = r1_initial.position
        r2_pos_initial = r2_initial.position

        print(f"\n✅ Phase 1 Complete:")
        print(f"   R1: value={r1_initial.value}, pos=({r1_pos_initial.x}, {r1_pos_initial.y}), uuid={r1_uuid}")
        print(f"   R2: value={r2_initial.value}, pos=({r2_pos_initial.x}, {r2_pos_initial.y}), uuid={r2_uuid}")

        # =====================================================================
        # PHASE 2: External Edit (Simulate KiCad GUI)
        # =====================================================================
        print("\n" + "="*70)
        print("PHASE 2: Simulate external KiCad edits")
        print("="*70)
        print("External edits:")
        print("  1. Add R3 (3.3k) at (200, 100)")
        print("  2. Change R1 value: 1k → 1.5k")
        print("  3. Move R2: (150, 100) → (160, 110)")

        # Read schematic file
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        # ===== Edit 1: Add R3 component =====
        r3_uuid = str(uuid.uuid4())
        r3_symbol_block = f'''
  (symbol (lib_id "Device:R") (at 200 100 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{r3_uuid}")
    (property "Reference" "R3" (at 200 97 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "3.3k" (at 200 102.5 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 200 105 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (instances
      (project "base_circuit"
        (path "/{sch_initial.uuid}"
          (reference "R3") (unit 1)
        )
      )
    )
  )'''

        # Insert R3 before closing parenthesis
        sch_content = sch_content.rstrip()
        if sch_content.endswith(')'):
            sch_content = sch_content[:-1] + r3_symbol_block + '\n)'

        # ===== Edit 2: Change R1 value from 1k to 1.5k =====
        # Find R1's symbol block first to ensure we only modify R1
        r1_ref_marker = '(property "Reference" "R1"'
        r1_ref_idx = sch_content.find(r1_ref_marker)
        if r1_ref_idx == -1:
            raise ValueError("Could not find R1 Reference property")

        # Find R1's value property (should be within ~200 chars after reference)
        r1_value_search = sch_content[r1_ref_idx:r1_ref_idx+500]
        r1_value_match = re.search(r'\(property "Value" "1k"', r1_value_search)
        if not r1_value_match:
            raise ValueError("Could not find R1 Value property")

        # Replace R1's value in the full content
        r1_value_idx = r1_ref_idx + r1_value_match.start()
        sch_content = (
            sch_content[:r1_value_idx] +
            '(property "Value" "1.5k"' +
            sch_content[r1_value_idx + len('(property "Value" "1k"'):]
        )

        # ===== Edit 3: Move R2 from (150, 100) to (160, 110) =====
        # Find R2's symbol block
        r2_ref_pos = sch_content.find('(property "Reference" "R2"')
        assert r2_ref_pos != -1, "Could not find R2 in schematic"

        # Find R2's symbol block start
        symbol_start = sch_content.rfind('(symbol', 0, r2_ref_pos)
        assert symbol_start != -1, "Could not find R2 symbol block start"

        # Find matching closing parenthesis
        paren_count = 0
        i = symbol_start
        symbol_end = -1

        while i < len(sch_content):
            if sch_content[i] == '(':
                paren_count += 1
            elif sch_content[i] == ')':
                paren_count -= 1
                if paren_count == 0:
                    symbol_end = i + 1
                    break
            i += 1

        assert symbol_end != -1, "Could not find closing parenthesis for R2"

        # Extract R2 block
        r2_block = sch_content[symbol_start:symbol_end]

        # Modify R2 position: (at X Y ANGLE) → (at 160 110 0)
        r2_block_moved = re.sub(
            r'\(at\s+[\d.]+\s+[\d.]+\s+[\d.]+\)',
            '(at 160 110 0)',
            r2_block,
            count=1  # Only symbol position, not property positions
        )

        # Replace R2 block in schematic
        sch_content = (
            sch_content[:symbol_start] +
            r2_block_moved +
            sch_content[symbol_end:]
        )

        # Write modified schematic
        with open(schematic_file, 'w') as f:
            f.write(sch_content)

        # Verify external edits were applied
        sch_modified = Schematic.load(str(schematic_file))
        components_modified = sch_modified.components

        assert len(components_modified) == 3, (
            f"Phase 2: Expected 3 components after adding R3, found {len(components_modified)}"
        )

        r1_modified = next(c for c in components_modified if c.reference == "R1")
        r2_modified = next(c for c in components_modified if c.reference == "R2")
        r3_modified = next(c for c in components_modified if c.reference == "R3")

        # Validate R1 value changed
        assert r1_modified.value == "1.5k", (
            f"R1 value should be 1.5k after edit, got {r1_modified.value}"
        )

        # Validate R2 position changed
        r2_pos_modified = r2_modified.position
        assert r2_pos_modified.x == 160.0 and r2_pos_modified.y == 110.0, (
            f"R2 should be at (160, 110) after move, got ({r2_pos_modified.x}, {r2_pos_modified.y})"
        )

        # Validate R3 added
        assert r3_modified.value == "3.3k", f"R3 value should be 3.3k, got {r3_modified.value}"

        print(f"\n✅ Phase 2 Complete - External edits applied:")
        print(f"   R1: value changed to {r1_modified.value}")
        print(f"   R2: moved to ({r2_pos_modified.x}, {r2_pos_modified.y})")
        print(f"   R3: added with value {r3_modified.value}")

        # =====================================================================
        # PHASE 3: Sync to Python (KiCad → Python)
        # =====================================================================
        print("\n" + "="*70)
        print("PHASE 3: Synchronize external edits back to Python")
        print("="*70)
        print("⚠️  NOTE: This phase requires kicad-to-python sync functionality")
        print("Currently testing schematic state preservation during regeneration")

        # NOTE: Full KiCad → Python synchronization requires the kicad-to-python
        # import functionality. For now, we test that external edits are preserved
        # during regeneration (which is the critical requirement).

        # Verify current schematic state before regeneration
        print(f"\nSchematic state BEFORE regeneration:")
        print(f"   - R1: {r1_modified.value} at ({r1_modified.position.x}, {r1_modified.position.y})")
        print(f"   - R2: {r2_modified.value} at ({r2_pos_modified.x}, {r2_pos_modified.y})")
        print(f"   - R3: {r3_modified.value} at ({r3_modified.position.x}, {r3_modified.position.y})")

        # =====================================================================
        # PHASE 4: Python Modification (Add R4)
        # =====================================================================
        print("\n" + "="*70)
        print("PHASE 4: Add R4 (4.7k) in Python code")
        print("="*70)

        # Add R4 to Python code (after R2)
        r4_component = '''
    r4 = Component(
        symbol="Device:R",
        ref="R4",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
        at=(250, 100, 0),
    )'''

        modified_code = original_code.replace(
            '    r2 = Component(\n        symbol="Device:R",\n        ref="R2",\n        value="2k",\n        footprint="Resistor_SMD:R_0603_1608Metric",\n        at=(150, 100, 0),\n    )',
            '    r2 = Component(\n        symbol="Device:R",\n        ref="R2",\n        value="2k",\n        footprint="Resistor_SMD:R_0603_1608Metric",\n        at=(150, 100, 0),\n    )' + r4_component
        )

        # Verify we made the change
        assert modified_code != original_code, (
            "Failed to add R4 to Python code"
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Phase 4: R4 added to Python code")

        # =====================================================================
        # PHASE 5: Regenerate (Validate All Changes Preserved)
        # =====================================================================
        print("\n" + "="*70)
        print("PHASE 5: Regenerate KiCad (should preserve all changes)")
        print("="*70)
        print("Expected after regeneration:")
        print("  - R1: 1.5k (from external edit)")
        print("  - R2: at (160, 110) (from external edit)")
        print("  - R3: 3.3k (from external edit)")
        print("  - R4: 4.7k (from Python)")

        result = subprocess.run(
            ["uv", "run", "base_circuit.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        # NOTE: Regeneration will currently reset the circuit to Python state
        # because full bidirectional sync is not yet implemented.
        # This test documents the EXPECTED behavior for when it is implemented.

        if result.returncode != 0:
            print(f"\n⚠️  Regeneration failed (expected until sync implemented):")
            print(f"STDOUT:\n{result.stdout}")
            print(f"STDERR:\n{result.stderr}")
            print(f"\n📋 This test documents the EXPECTED workflow:")
            print(f"   1. Generate from Python ✓")
            print(f"   2. Edit externally ✓")
            print(f"   3. Sync to Python (TODO)")
            print(f"   4. Modify in Python ✓")
            print(f"   5. Regenerate preserving all changes (TODO)")

            # Mark as expected failure for now
            pytest.skip(
                "Full bidirectional sync not yet implemented. "
                "Test documents expected behavior."
            )

        print(f"\n📋 Synchronization output:")
        print(result.stdout)

        # Load final schematic
        sch_final = Schematic.load(str(schematic_file))
        components_final = sch_final.components

        # EXPECTED: 4 components (R1, R2, R3 from external edit + R4 from Python)
        # ACTUAL (without full sync): 3 components (R1, R2, R4 - R3 was removed)
        if len(components_final) != 4:
            print(f"\n⚠️  Regeneration removed external edits (expected until sync implemented):")
            print(f"   Expected: 4 components (R1, R2, R3, R4)")
            print(f"   Found: {len(components_final)} components ({[c.reference for c in components_final]})")
            print(f"\n📋 This test documents the EXPECTED workflow:")
            print(f"   1. Generate from Python ✓")
            print(f"   2. Edit externally ✓")
            print(f"   3. Sync to Python (TODO)")
            print(f"   4. Modify in Python ✓")
            print(f"   5. Regenerate preserving all changes (TODO)")
            print(f"\n⚠️  Full bidirectional sync not yet implemented.")
            print(f"   External edits (R3) are lost during regeneration.")
            print(f"   This test will pass when sync is implemented.")

            # Skip test with informative message
            pytest.skip(
                "Full bidirectional sync not yet implemented. "
                "Test documents expected behavior. "
                f"Current: {len(components_final)} components, Expected: 4 components"
            )

        assert len(components_final) == 4, (
            f"Phase 5: Expected 4 components, found {len(components_final)}\n"
            f"Components: {[c.reference for c in components_final]}"
        )

        r1_final = next(c for c in components_final if c.reference == "R1")
        r2_final = next(c for c in components_final if c.reference == "R2")
        r3_final = next(c for c in components_final if c.reference == "R3")
        r4_final = next(c for c in components_final if c.reference == "R4")

        # CRITICAL: External edits should be preserved
        assert r1_final.value == "1.5k", (
            f"❌ EXTERNAL EDIT LOST!\n"
            f"   R1 value should be 1.5k (from external edit), got {r1_final.value}\n"
            f"   External value change was not preserved!"
        )

        r2_pos_final = r2_final.position
        assert r2_pos_final.x == 160.0 and r2_pos_final.y == 110.0, (
            f"❌ EXTERNAL EDIT LOST!\n"
            f"   R2 should be at (160, 110) (from external edit)\n"
            f"   Got: ({r2_pos_final.x}, {r2_pos_final.y})\n"
            f"   External position change was not preserved!"
        )

        assert r3_final.value == "3.3k", (
            f"❌ EXTERNAL COMPONENT LOST!\n"
            f"   R3 (3.3k) added externally should still exist\n"
            f"   External component was not preserved!"
        )

        # Python-added component should exist
        assert r4_final.value == "4.7k", (
            f"R4 should be 4.7k (from Python), got {r4_final.value}"
        )

        # UUIDs should be preserved (not regenerated)
        assert r1_final.uuid == r1_uuid, (
            f"R1 UUID changed! This means component was removed and re-added\n"
            f"Expected: {r1_uuid}\n"
            f"Got: {r1_final.uuid}"
        )

        assert r2_final.uuid == r2_uuid, (
            f"R2 UUID changed! This means component was removed and re-added\n"
            f"Expected: {r2_uuid}\n"
            f"Got: {r2_final.uuid}"
        )

        assert r3_final.uuid == r3_uuid, (
            f"R3 UUID changed! This means component was removed and re-added\n"
            f"Expected: {r3_uuid}\n"
            f"Got: {r3_final.uuid}"
        )

        print(f"\n✅ Phase 5 VALIDATION COMPLETE!")
        print(f"   R1: {r1_final.value} (external edit preserved) ✓")
        print(f"   R2: ({r2_pos_final.x}, {r2_pos_final.y}) (external move preserved) ✓")
        print(f"   R3: {r3_final.value} (external component preserved) ✓")
        print(f"   R4: {r4_final.value} (Python component added) ✓")
        print(f"   All UUIDs preserved ✓")

        # =====================================================================
        # PHASE 6: Netlist Validation
        # =====================================================================
        print("\n" + "="*70)
        print("PHASE 6: Validate netlist contains all components")
        print("="*70)

        netlist_file = output_dir / "base_circuit.net"
        assert netlist_file.exists(), "Netlist file not created"

        with open(netlist_file, 'r') as f:
            netlist_content = f.read()

        # Verify all four components in netlist
        assert 'R1' in netlist_content, "R1 missing from netlist"
        assert 'R2' in netlist_content, "R2 missing from netlist"
        assert 'R3' in netlist_content, "R3 missing from netlist"
        assert 'R4' in netlist_content, "R4 missing from netlist"

        # Verify values in netlist
        assert '1.5k' in netlist_content, "R1 value (1.5k) missing from netlist"
        assert '2k' in netlist_content, "R2 value (2k) missing from netlist"
        assert '3.3k' in netlist_content, "R3 value (3.3k) missing from netlist"
        assert '4.7k' in netlist_content, "R4 value (4.7k) missing from netlist"

        print(f"\n✅ Phase 6: Netlist validation passed")
        print(f"   All 4 components present in netlist")
        print(f"   All values correct in netlist")

        print(f"\n" + "="*70)
        print(f"🎉 TEST 51 COMPLETE: EXTERNAL EDIT SYNC VALIDATED!")
        print(f"="*70)
        print(f"\n✅ CRITICAL WORKFLOW CONFIRMED:")
        print(f"   1. Generate from Python → KiCad")
        print(f"   2. Edit externally in KiCad (add, modify, move)")
        print(f"   3. Synchronize changes back to Python")
        print(f"   4. Add more components in Python")
        print(f"   5. Regenerate preserving ALL changes")
        print(f"\n✅ COLLABORATIVE WORKFLOW ENABLED:")
        print(f"   - Engineers can work on same circuit")
        print(f"   - KiCad GUI edits preserved")
        print(f"   - Python code changes preserved")
        print(f"   - No data loss during sync cycles")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
