#!/usr/bin/env python3
"""
Test 13: Component rename consistency across tools.

Tests: Renaming a component and ensuring references stay consistent.

Real-world scenario:
- User creates R1 in Python
- Opens in KiCad, renames to R_PULLUP (more descriptive)
- Imports back to Python
- Adds connection to R_PULLUP
- Does the renamed reference work correctly?

Steps:
1. Create circuit with R1
2. Generate KiCad
3. Simulate rename R1 → R_PULLUP in KiCad
4. Import back to Python
5. Verify renamed reference in Python
6. Add connection using new name
7. Regenerate KiCad
8. Verify consistency

Does NOT test: Automatic reference annotation
"""

from pathlib import Path
import sys
import re

# Add parent directory to path for test_utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_utils import (
    clean_output_dir,
    copy_to_output,
    run_python_circuit,
    import_kicad_to_python,
    assert_kicad_project_exists,
    assert_component_in_schematic,
    get_test_output_dir,
    print_test_header,
    print_test_footer,
)


def test_component_rename():
    """
    Test: Component rename consistency.

    Critical for collaborative workflows where names evolve.
    """
    print_test_header("13: Component Rename Consistency")

    # Setup
    test_file = Path(__file__)
    output_dir = get_test_output_dir(test_file, "13_component_rename")
    clean_output_dir(output_dir)

    # Step 1: Generate initial circuit
    print("Step 1: Generating initial circuit with R1...")
    fixture = Path(__file__).parent / "single_resistor.py"
    circuit_file = copy_to_output(fixture, output_dir, "step1_initial.py")

    exit_code, stdout, stderr = run_python_circuit(circuit_file)
    if exit_code != 0:
        print(f"❌ Generation failed: {stderr}")
        print_test_footer(success=False)
        assert False

    kicad_dir = output_dir / "single_resistor"
    kicad_pro = assert_kicad_project_exists(kicad_dir, "single_resistor")
    kicad_sch = kicad_dir / "single_resistor.kicad_sch"
    print(f"✅ Generated with R1")

    # Step 2: Simulate rename in KiCad (R1 → R_PULLUP)
    print("\nStep 2: Simulating KiCad rename R1 → R_PULLUP...")
    sch_content = kicad_sch.read_text()

    # Replace all instances of "R1" reference
    sch_content = sch_content.replace('"Reference" "R1"', '"Reference" "R_PULLUP"')

    kicad_sch.write_text(sch_content)
    print("✅ Renamed R1 → R_PULLUP in KiCad")

    # Verify rename
    if '"Reference" "R_PULLUP"' in kicad_sch.read_text():
        print("   ✅ Rename verified in schematic")
    else:
        print("   ❌ Rename failed")
        print_test_footer(success=False)
        assert False

    # Step 3: Import back to Python
    print("\nStep 3: Importing renamed circuit to Python...")
    imported_py = output_dir / "step3_imported.py"
    exit_code, stdout, stderr = import_kicad_to_python(kicad_pro, imported_py)

    if exit_code != 0:
        print(f"❌ Import failed: {stderr}")
        print_test_footer(success=False)
        assert False

    print(f"✅ Imported to: {imported_py}")

    # Step 4: Verify new reference in Python
    print("\nStep 4: Verifying renamed reference in Python...")
    py_content = imported_py.read_text()

    has_new_ref = 'ref="R_PULLUP"' in py_content or "ref='R_PULLUP'" in py_content
    has_old_ref = 'ref="R1"' in py_content or "ref='R1'" in py_content

    if has_new_ref and not has_old_ref:
        print("   ✅ Python has R_PULLUP (renamed correctly)")
    elif has_old_ref:
        print("   ❌ Python still has R1 (rename not preserved)")
        print_test_footer(success=False)
        assert False, "Rename not preserved in Python import"
    else:
        print("   ⚠️  Could not find reference in Python")

    # Step 5: Add connection using renamed reference
    print("\nStep 5: Adding connection using renamed reference...")

    # Add second component and connect to renamed R_PULLUP
    py_content_with_connection = py_content.replace(
        'r_pullup = Component(symbol="Device:R", ref="R_PULLUP", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")',
        '''r_pullup = Component(symbol="Device:R", ref="R_PULLUP", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")

    # Add R2 and connect to renamed R_PULLUP
    r2 = Component(symbol="Device:R", ref="R2", value="20k", footprint="Resistor_SMD:R_0603_1608Metric")

    # Connection using renamed reference
    from circuit_synth import Net
    net1 = Net("SIGNAL")
    net1 += r_pullup["2"]
    net1 += r2["1"]'''
    )

    imported_py.write_text(py_content_with_connection)
    print("   ✅ Added R2 with connection to R_PULLUP")

    # Step 6: Regenerate KiCad
    print("\nStep 6: Regenerating KiCad...")
    exit_code, stdout, stderr = run_python_circuit(imported_py)

    if exit_code != 0:
        print(f"❌ Regeneration failed: {stderr}")
        print(f"   This likely means renamed reference caused errors")
        print_test_footer(success=False)
        assert False, f"Regeneration with renamed reference failed: {stderr}"

    print(f"✅ KiCad regenerated successfully")

    # Step 7: Verify final state
    print("\nStep 7: Verifying final state...")
    final_sch = kicad_sch.read_text()

    # Check both components exist with correct references
    has_pullup = '"Reference" "R_PULLUP"' in final_sch
    has_r2 = '"Reference" "R2"' in final_sch
    has_signal_net = '"SIGNAL"' in final_sch or "'SIGNAL'" in final_sch

    if has_pullup:
        print("   ✅ R_PULLUP present (renamed reference preserved)")
    else:
        print("   ❌ R_PULLUP missing")

    if has_r2:
        print("   ✅ R2 present")
    else:
        print("   ❌ R2 missing")

    if has_signal_net:
        print("   ✅ SIGNAL net present")
    else:
        print("   ⚠️  SIGNAL net not found")

    success = has_pullup and has_r2

    # Summary
    print("\n📊 Component Rename Summary:")
    print("-" * 60)
    print("Workflow:")
    print("  1. Created R1 in Python")
    print("  2. Renamed R1 → R_PULLUP in KiCad")
    print("  3. Imported to Python (got R_PULLUP)")
    print("  4. Added R2 with connection to R_PULLUP")
    print("  5. Regenerated KiCad")
    print()
    print("Final state:")
    print(f"  - R_PULLUP present: {'✅' if has_pullup else '❌'}")
    print(f"  - R2 present: {'✅' if has_r2 else '❌'}")
    print(f"  - Connection: {'✅' if has_signal_net else '⚠️'}")
    print()
    if success:
        print("Result: ✅ RENAME CONSISTENCY WORKS")
    else:
        print("Result: ❌ RENAME CONSISTENCY BROKEN")
    print("-" * 60)

    print_test_footer(success=success)
    if not success:
        assert False, "Component rename consistency failed"


if __name__ == "__main__":
    test_component_rename()
