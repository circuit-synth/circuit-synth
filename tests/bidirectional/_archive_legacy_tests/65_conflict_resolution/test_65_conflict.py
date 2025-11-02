#!/usr/bin/env python3
"""
Automated test for 65_conflict_resolution bidirectional test.

Tests conflict resolution behavior when same component is modified in both
Python and KiCad without intermediate synchronization:

1. Generate initial circuit (R1=10k, R2=1k)
2. Manually edit KiCad schematic (R1→22k, add R4)
3. Edit Python WITHOUT importing (R1→47k, add R3)
4. Regenerate from Python
5. Document observed behavior:
   - Which R1 value wins? (Python or KiCad)
   - Is R3 present? (Python-only addition)
   - Is R4 present? (KiCad-only addition)
   - Are there conflict warnings?

Validation uses kicad-sch-api to verify schematic structure.

Real-world workflow: Developer forgets to import KiCad changes before editing
Python, or team collaboration with concurrent edits.

NOTE: This test documents CURRENT BEHAVIOR, which is likely "Python wins"
without conflict detection. Future enhancement would add conflict warnings.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_65_conflict_resolution(request):
    """Test conflict resolution when same component modified in Python and KiCad.

    Workflow:
    1. Generate initial KiCad (R1=10k, R2=1k)
    2. Manually edit KiCad schematic (R1→22k, add R4=100k)
    3. Edit Python code WITHOUT importing (R1→47k, add R3=4.7k)
    4. Regenerate from Python → document which changes survive
    5. Analyze conflict resolution strategy

    Level 2 Semantic Validation:
    - kicad-sch-api for schematic component validation
    - Conflict detection behavior documentation
    - Resolution strategy validation
    - Data loss detection (KiCad-only changes)

    NOTE: Test documents behavior, may not strictly pass/fail.
    Current expected behavior: Python wins, no conflict warnings.
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "conflicting_edits.py"
    output_dir = test_dir / "conflicting_edits"
    schematic_file = output_dir / "conflicting_edits.kicad_sch"

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
        # STEP 1: Generate initial KiCad (R1=10k, R2=1k)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate initial KiCad (R1=10k, R2=1k)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "conflicting_edits.py"],
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

        # Validate initial state using kicad-sch-api
        from kicad_sch_api import Schematic

        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 2, (
            f"Step 1: Expected 2 components (R1, R2), found {len(components)}"
        )

        # Verify R1 and R2
        refs = {c.reference for c in components}
        assert refs == {"R1", "R2"}, (
            f"Step 1: Expected references {{R1, R2}}, found {refs}"
        )

        r1_initial = next(c for c in components if c.reference == "R1")
        r2_initial = next(c for c in components if c.reference == "R2")

        assert r1_initial.value == "10k", (
            f"Step 1: R1 value should be 10k, found {r1_initial.value}"
        )
        assert r2_initial.value == "1k", (
            f"Step 1: R2 value should be 1k, found {r2_initial.value}"
        )

        print(f"✅ Step 1: Initial state validated")
        print(f"   - R1: {r1_initial.value}")
        print(f"   - R2: {r2_initial.value}")
        print(f"   - Total components: {len(components)}")

        # =====================================================================
        # STEP 2: Manually edit KiCad schematic (R1→22k, add R4)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Manually edit KiCad schematic (R1→22k, add R4)")
        print("="*70)

        # Read schematic file as text
        with open(schematic_file, "r") as f:
            sch_content = f.read()

        # Change R1 value from 10k to 22k
        # Find the property line for R1's value
        sch_content = re.sub(
            r'(\(symbol.*?reference "R1".*?)(property "Value" "10k")',
            r'\1(property "Value" "22k")',
            sch_content,
            flags=re.DOTALL
        )

        # Add R4 component (simplified - add after R2)
        # This is a minimal R4 addition for testing
        r4_component = '''
  (symbol (lib_id "Device:R") (at 50.8 38.1 0) (unit 1)
    (in_bom yes) (on_board yes) (dnp no)
    (uuid "r4-test-uuid-12345678")
    (property "Reference" "R4" (at 52.07 36.83 0)
      (effects (font (size 1.27 1.27)) (justify left))
    )
    (property "Value" "100k" (at 52.07 39.37 0)
      (effects (font (size 1.27 1.27)) (justify left))
    )
    (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 49.022 38.1 90)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Datasheet" "~" (at 50.8 38.1 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (pin "1" (uuid "r4-pin1-uuid"))
    (pin "2" (uuid "r4-pin2-uuid"))
    (instances
      (project "conflicting_edits"
        (path "/sheet-path" (reference "R4") (unit 1))
      )
    )
  )
'''
        # Insert R4 before the closing of the sheet
        sch_content = sch_content.replace(
            '\n)\n',
            r4_component + '\n)\n',
            1  # Only replace first occurrence
        )

        # Write modified schematic back
        with open(schematic_file, "w") as f:
            f.write(sch_content)

        # Verify KiCad changes using kicad-sch-api
        sch_modified = Schematic.load(str(schematic_file))
        components_modified = sch_modified.components

        # Should now have R1(22k), R2(1k), R4(100k)
        refs_modified = {c.reference for c in components_modified}

        r1_kicad = next((c for c in components_modified if c.reference == "R1"), None)
        r4_kicad = next((c for c in components_modified if c.reference == "R4"), None)

        # Note: Some parsers might not pick up manually added components correctly
        # Document what we actually see
        print(f"✅ Step 2: KiCad manually edited")
        print(f"   - R1 value changed to: {r1_kicad.value if r1_kicad else 'NOT FOUND'}")
        print(f"   - R4 added: {'YES' if r4_kicad else 'NO'}")
        print(f"   - References: {refs_modified}")
        print(f"   - Total components: {len(components_modified)}")

        # =====================================================================
        # STEP 3: Edit Python WITHOUT importing (R1→47k, add R3)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Edit Python WITHOUT importing (R1→47k, add R3)")
        print("="*70)

        # Modify Python code:
        # 1. Change R1 value from 10k to 47k
        # 2. Uncomment R3

        modified_code = original_code.replace(
            'value="10k",  # CONFLICT:',
            'value="47k",  # CONFLICT:'
        )

        # Uncomment R3
        modified_code = re.sub(
            r'# (r3 = Component\()',
            r'\1',
            modified_code
        )
        modified_code = re.sub(
            r'#(\s+)(symbol=|ref=|value=|footprint=|\))',
            r'\1\2',
            modified_code
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 3: Python code modified")
        print(f"   - R1 value changed to: 47k (in Python)")
        print(f"   - R3 added: YES (in Python)")
        print(f"   - KiCad NOT imported (conflict created)")

        # =====================================================================
        # STEP 4: Regenerate from Python (CONFLICT!)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Regenerate from Python (creates conflict)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "conflicting_edits.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration with conflicts\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Capture output for conflict warning analysis
        output = result.stdout + result.stderr

        # Check for conflict warnings
        has_conflict_warning = (
            "CONFLICT" in output or
            "conflict" in output.lower() or
            "WARNING" in output or
            "warning" in output.lower()
        )

        print(f"✅ Step 4: Regeneration completed")
        print(f"   - Conflict warnings detected: {'YES' if has_conflict_warning else 'NO'}")

        # =====================================================================
        # STEP 5: Analyze final state - document behavior
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Analyze conflict resolution behavior")
        print("="*70)

        # Load final schematic
        sch_final = Schematic.load(str(schematic_file))
        components_final = sch_final.components

        refs_final = {c.reference for c in components_final}

        r1_final = next((c for c in components_final if c.reference == "R1"), None)
        r2_final = next((c for c in components_final if c.reference == "R2"), None)
        r3_final = next((c for c in components_final if c.reference == "R3"), None)
        r4_final = next((c for c in components_final if c.reference == "R4"), None)

        # Document findings
        print(f"\nFinal State Analysis:")
        print(f"  - R1 value: {r1_final.value if r1_final else 'NOT FOUND'}")
        print(f"    (Python wanted: 47k, KiCad had: 22k)")
        print(f"  - R2 value: {r2_final.value if r2_final else 'NOT FOUND'}")
        print(f"    (Unchanged - control)")
        print(f"  - R3 present: {'YES' if r3_final else 'NO'}")
        print(f"    (Added in Python only)")
        print(f"  - R4 present: {'YES' if r4_final else 'NO'}")
        print(f"    (Added in KiCad only)")
        print(f"  - Total components: {len(components_final)}")
        print(f"  - References: {sorted(refs_final)}")

        # =====================================================================
        # STEP 6: Validate expected behavior (PYTHON WINS)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Validate conflict resolution strategy")
        print("="*70)

        # Expected behavior: Python wins (overwrites KiCad)
        # This documents CURRENT behavior, not necessarily ideal behavior

        # R1 should have Python's value (47k), not KiCad's (22k)
        if r1_final:
            python_wins_r1 = r1_final.value == "47k"
            print(f"  R1 value resolution: {'PYTHON WINS' if python_wins_r1 else 'KICAD WINS or OTHER'}")
            print(f"    - Final value: {r1_final.value}")
            print(f"    - Python wanted: 47k")
            print(f"    - KiCad had: 22k")
        else:
            print(f"  R1 value resolution: ERROR - R1 not found!")
            python_wins_r1 = False

        # R3 should be present (Python addition)
        python_addition_preserved = r3_final is not None
        print(f"  R3 (Python addition): {'PRESENT' if python_addition_preserved else 'MISSING'}")

        # R4 likely lost (KiCad-only addition, not in Python)
        kicad_addition_lost = r4_final is None
        print(f"  R4 (KiCad addition): {'LOST' if kicad_addition_lost else 'PRESERVED'}")

        # Conflict warnings
        print(f"  Conflict warnings: {'YES' if has_conflict_warning else 'NO'}")

        # =====================================================================
        # SUMMARY
        # =====================================================================
        print("\n" + "="*70)
        print("TEST SUMMARY: CONFLICT RESOLUTION")
        print("="*70)
        print(f"\nConflict Scenario:")
        print(f"  - Python: R1→47k, +R3")
        print(f"  - KiCad:  R1→22k, +R4")
        print(f"\nObserved Behavior:")
        print(f"  - R1 value: {r1_final.value if r1_final else 'ERROR'} ({'Python wins' if python_wins_r1 else 'Unexpected'})")
        print(f"  - R3 present: {'YES' if python_addition_preserved else 'NO'}")
        print(f"  - R4 present: {'YES' if not kicad_addition_lost else 'NO'} ({'LOST' if kicad_addition_lost else 'Preserved'})")
        print(f"  - Conflict warnings: {'YES' if has_conflict_warning else 'NO'}")
        print(f"\nResolution Strategy: {'PYTHON-WINS (overwrite)' if python_wins_r1 and kicad_addition_lost else 'UNKNOWN'}")

        if python_wins_r1 and kicad_addition_lost and not has_conflict_warning:
            print(f"\n⚠️  Current Behavior: Python overwrites KiCad without warning")
            print(f"   - Manual KiCad edits are lost")
            print(f"   - No conflict detection")
            print(f"   - Recommendation: Add conflict detection and user warning")
        elif python_wins_r1 and has_conflict_warning:
            print(f"\n✅ Good: Conflict detected with warning")
            print(f"   - User notified of potential data loss")
        else:
            print(f"\n❓ Unexpected behavior - document for investigation")

        print(f"\n{'='*70}")
        print(f"🎉 Test 65: Conflict Resolution - BEHAVIOR DOCUMENTED")
        print(f"{'='*70}")

        # Test passes if it documents the behavior correctly
        # Not strict pass/fail, but verification that behavior is as expected
        assert r1_final is not None, "R1 must exist in final schematic"
        assert r2_final is not None, "R2 must exist in final schematic"

        # Document that Python-wins is current behavior
        # (These are soft assertions - document behavior)
        if not python_wins_r1:
            print(f"\n⚠️  NOTE: Expected Python to win R1 conflict, but got {r1_final.value}")

        if not kicad_addition_lost:
            print(f"\n⚠️  NOTE: Expected R4 (KiCad-only) to be lost, but it was preserved")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    # Allow running test directly
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))
