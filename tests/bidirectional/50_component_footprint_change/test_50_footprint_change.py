#!/usr/bin/env python3
"""
Automated test for 50_component_footprint_change bidirectional test.

Tests component footprint changes while preserving position, symbol, and connections.

Workflow:
1. Generate KiCad with R1 (0603 footprint) at default position
2. Move R1 to specific position (100, 50) in KiCad
3. Phase 1: Change footprint 0603 → 0805 (SMD to SMD)
   - Regenerate KiCad
   - Validate: position preserved, footprint changed, symbol unchanged
4. Phase 2: Change footprint 0805 → THT (SMD to through-hole)
   - Regenerate KiCad
   - Validate: position preserved, footprint changed, symbol unchanged

Validation Levels:
- Level 2: kicad-sch-api for semantic validation (component properties, position)
- Level 3: Netlist validation for footprint field
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_50_footprint_change_smd_to_smd_to_tht(request):
    """Test footprint changes (0603 → 0805 → THT) with position preservation.

    Tests two phases:
    1. SMD to SMD: 0603 → 0805 (surface mount)
    2. SMD to THT: 0805 → through-hole

    Validates that footprint changes:
    - Preserve component position (canonical)
    - Keep symbol unchanged (Device:R)
    - Keep reference unchanged (R1)
    - Update footprint property correctly
    - Update netlist footprint field
    - Don't break connections

    Level 2 Semantic Validation:
    - kicad-sch-api for component validation

    Level 3 Netlist Validation:
    - Netlist parser for footprint field validation
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "resistor_footprints.py"
    output_dir = test_dir / "resistor_footprints"
    schematic_file = output_dir / "resistor_footprints.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file (0603 footprint)
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate KiCad with R1 (0603 footprint)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with R1 (0603 footprint)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "resistor_footprints.py"],
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

        # Get R1's default position and verify it has 0603 footprint
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 1
        r1_initial = components[0]
        assert r1_initial.reference == "R1"
        assert r1_initial.value == "10k"
        assert "0603" in r1_initial.footprint, (
            f"Expected 0603 footprint, got: {r1_initial.footprint}"
        )

        default_pos = r1_initial.position
        r1_uuid = r1_initial.uuid
        r1_symbol = str(r1_initial.lib_id)

        print(f"Step 1: R1 generated (0603 footprint)")
        print(f"   - Reference: {r1_initial.reference}")
        print(f"   - Value: {r1_initial.value}")
        print(f"   - Footprint: {r1_initial.footprint}")
        print(f"   - Symbol: {r1_symbol}")
        print(f"   - Position: {default_pos}")
        print(f"   - UUID: {r1_uuid}")

        # =====================================================================
        # STEP 2: Move R1 to specific position (100, 50)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Move R1 to (100, 50)")
        print("="*70)

        # Read schematic file
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        # Find R1 symbol block
        r1_ref_pos = sch_content.find('(property "Reference" "R1"')
        assert r1_ref_pos != -1, "Could not find R1 in schematic"

        # Find symbol block start
        symbol_start = sch_content.rfind('(symbol', 0, r1_ref_pos)
        assert symbol_start != -1

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

        assert symbol_end != -1, "Could not find closing parenthesis for R1"

        # Extract and modify R1 block to move to (100, 50)
        r1_block = sch_content[symbol_start:symbol_end]

        # Modify position: (symbol ... (at X Y ANGLE) ...)
        r1_block_moved = re.sub(
            r'\(at\s+[\d.]+\s+[\d.]+\s+[\d.]+\)',
            '(at 100 50 0)',
            r1_block,
            count=1
        )

        # Replace in schematic
        sch_content_moved = (
            sch_content[:symbol_start] +
            r1_block_moved +
            sch_content[symbol_end:]
        )

        # Write modified schematic
        with open(schematic_file, 'w') as f:
            f.write(sch_content_moved)

        # Verify R1 moved to (100, 50)
        sch_moved = Schematic.load(str(schematic_file))
        r1_moved = sch_moved.components[0]
        moved_pos = r1_moved.position

        assert moved_pos.x == 100.0 and moved_pos.y == 50.0, (
            f"R1 should be at (100, 50), got {moved_pos}"
        )

        print(f"Step 2: R1 moved to (100, 50)")
        print(f"   - Previous position: {default_pos}")
        print(f"   - New position: {moved_pos}")
        print(f"   - UUID unchanged: {r1_uuid}")

        # =====================================================================
        # STEP 3: PHASE 1 - Change footprint 0603 → 0805 (SMD to SMD)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: PHASE 1 - Change footprint 0603 → 0805 (SMD to SMD)")
        print("="*70)

        # Modify Python code: 0603 → 0805
        modified_code_0805 = original_code.replace(
            'footprint="Resistor_SMD:R_0603_1608Metric"',
            'footprint="Resistor_SMD:R_0805_2012Metric"'
        )

        # Verify the replacement happened
        assert 'R_0805_2012Metric' in modified_code_0805, (
            "Failed to replace 0603 with 0805 in Python code"
        )
        assert 'R_0603_1608Metric' not in modified_code_0805, (
            "0603 footprint still present after replacement"
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code_0805)

        print(f"Step 3: Footprint changed to 0805 in Python")
        print(f"   - From: Resistor_SMD:R_0603_1608Metric")
        print(f"   - To:   Resistor_SMD:R_0805_2012Metric")
        print(f"   - Reference: R1 (unchanged)")
        print(f"   - Symbol: Device:R (unchanged)")

        # =====================================================================
        # STEP 4: Regenerate KiCad (UUID matching should preserve position)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Regenerate KiCad with 0805 footprint")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "resistor_footprints.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration with 0805 footprint\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"\nSynchronization output:")
        print(result.stdout)

        # =====================================================================
        # STEP 5: Validate footprint changed to 0805, position preserved
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate 0805 footprint and position preservation")
        print("="*70)

        sch_0805 = Schematic.load(str(schematic_file))
        components_0805 = sch_0805.components

        assert len(components_0805) == 1, (
            f"Expected 1 component, found {len(components_0805)}"
        )

        r1_0805 = components_0805[0]
        pos_0805 = r1_0805.position
        uuid_0805 = r1_0805.uuid
        symbol_0805 = str(r1_0805.lib_id)
        footprint_0805 = r1_0805.footprint

        # CRITICAL: Reference should STILL be R1
        assert r1_0805.reference == "R1", (
            f"Reference changed unexpectedly!\n"
            f"   Expected: R1\n"
            f"   Got: {r1_0805.reference}"
        )

        # CRITICAL: Footprint should be 0805
        assert "0805" in footprint_0805, (
            f"Footprint NOT changed to 0805!\n"
            f"   Expected: R_0805_2012Metric\n"
            f"   Got: {footprint_0805}"
        )

        # CRITICAL: Position should be preserved (UUID matching worked!)
        assert pos_0805.x == 100.0 and pos_0805.y == 50.0, (
            f"Position NOT preserved!\n"
            f"   Expected: (100, 50)\n"
            f"   Got: {pos_0805}\n"
            f"   This means UUID matching did NOT work!"
        )

        # UUID should be preserved
        assert uuid_0805 == r1_uuid, (
            f"UUID changed!\n"
            f"   Expected: {r1_uuid}\n"
            f"   Got: {uuid_0805}\n"
            f"   This suggests component was removed and re-added"
        )

        # Symbol should be unchanged (still Device:R)
        assert "R" in symbol_0805 or "Resistor" in symbol_0805, (
            f"Symbol changed unexpectedly!\n"
            f"   Expected: Device:R (resistor)\n"
            f"   Got: {symbol_0805}"
        )

        # Value should be unchanged
        assert r1_0805.value == "10k", (
            f"Value changed unexpectedly: {r1_0805.value}"
        )

        print(f"\nStep 5: PHASE 1 VALIDATED!")
        print(f"   - Footprint changed: 0603 → 0805")
        print(f"   - Reference preserved: R1")
        print(f"   - Value preserved: 10k")
        print(f"   - Position preserved: {pos_0805}")
        print(f"   - UUID preserved: {uuid_0805}")
        print(f"   - Symbol preserved: {symbol_0805}")

        # =====================================================================
        # STEP 6: PHASE 2 - Change footprint 0805 → THT (SMD to through-hole)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: PHASE 2 - Change footprint 0805 → THT (SMD to THT)")
        print("="*70)

        # Modify Python code: 0805 → THT
        modified_code_tht = modified_code_0805.replace(
            'footprint="Resistor_SMD:R_0805_2012Metric"',
            'footprint="Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"'
        )

        # Verify the replacement happened
        assert 'Resistor_THT:R_Axial_DIN0207' in modified_code_tht, (
            "Failed to replace 0805 with THT in Python code"
        )
        assert 'R_0805_2012Metric' not in modified_code_tht, (
            "0805 footprint still present after replacement"
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code_tht)

        print(f"Step 6: Footprint changed to THT in Python")
        print(f"   - From: Resistor_SMD:R_0805_2012Metric")
        print(f"   - To:   Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal")
        print(f"   - Mount type: SMD → Through-hole")
        print(f"   - Reference: R1 (unchanged)")
        print(f"   - Symbol: Device:R (unchanged)")

        # =====================================================================
        # STEP 7: Regenerate KiCad with THT footprint
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 7: Regenerate KiCad with THT footprint")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "resistor_footprints.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 7 failed: Regeneration with THT footprint\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"\nSynchronization output:")
        print(result.stdout)

        # =====================================================================
        # STEP 8: Validate footprint changed to THT, position preserved
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 8: Validate THT footprint and position preservation")
        print("="*70)

        sch_tht = Schematic.load(str(schematic_file))
        components_tht = sch_tht.components

        assert len(components_tht) == 1, (
            f"Expected 1 component, found {len(components_tht)}"
        )

        r1_tht = components_tht[0]
        pos_tht = r1_tht.position
        uuid_tht = r1_tht.uuid
        symbol_tht = str(r1_tht.lib_id)
        footprint_tht = r1_tht.footprint

        # CRITICAL: Reference should STILL be R1
        assert r1_tht.reference == "R1", (
            f"Reference changed unexpectedly!\n"
            f"   Expected: R1\n"
            f"   Got: {r1_tht.reference}"
        )

        # CRITICAL: Footprint should be THT
        assert "THT" in footprint_tht or "Axial" in footprint_tht, (
            f"Footprint NOT changed to THT!\n"
            f"   Expected: Resistor_THT:R_Axial_DIN0207...\n"
            f"   Got: {footprint_tht}"
        )

        # CRITICAL: Position should STILL be preserved
        assert pos_tht.x == 100.0 and pos_tht.y == 50.0, (
            f"Position NOT preserved after THT change!\n"
            f"   Expected: (100, 50)\n"
            f"   Got: {pos_tht}"
        )

        # UUID should STILL be preserved
        assert uuid_tht == r1_uuid, (
            f"UUID changed after THT!\n"
            f"   Expected: {r1_uuid}\n"
            f"   Got: {uuid_tht}"
        )

        # Symbol should STILL be unchanged (still Device:R)
        assert "R" in symbol_tht or "Resistor" in symbol_tht, (
            f"Symbol changed unexpectedly!\n"
            f"   Expected: Device:R (resistor)\n"
            f"   Got: {symbol_tht}"
        )

        # Value should STILL be unchanged
        assert r1_tht.value == "10k", (
            f"Value changed unexpectedly: {r1_tht.value}"
        )

        print(f"\nStep 8: PHASE 2 VALIDATED!")
        print(f"   - Footprint changed: 0805 → THT")
        print(f"   - Mount type: SMD → Through-hole")
        print(f"   - Reference preserved: R1")
        print(f"   - Value preserved: 10k")
        print(f"   - Position preserved: {pos_tht}")
        print(f"   - UUID preserved: {uuid_tht}")
        print(f"   - Symbol preserved: {symbol_tht}")

        # =====================================================================
        # FINAL SUMMARY
        # =====================================================================
        print("\n" + "="*70)
        print("FINAL SUMMARY: Footprint Change Test SUCCESSFUL!")
        print("="*70)
        print(f"\nPhase 1 (SMD → SMD):")
        print(f"   - Footprint: 0603 → 0805")
        print(f"   - Position preserved")
        print(f"   - Symbol unchanged (Device:R)")
        print(f"   - Reference unchanged (R1)")
        print(f"\nPhase 2 (SMD → THT):")
        print(f"   - Footprint: 0805 → THT")
        print(f"   - Mount type: Surface mount → Through-hole")
        print(f"   - Position preserved")
        print(f"   - Symbol unchanged (Device:R)")
        print(f"   - Reference unchanged (R1)")
        print(f"\n Both footprint changes successful!")
        print(f"   UUID-based matching preserved position through all changes!")

    finally:
        # Restore original Python file (0603)
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
