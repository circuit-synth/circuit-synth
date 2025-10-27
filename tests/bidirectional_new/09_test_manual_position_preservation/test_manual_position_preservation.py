#!/usr/bin/env python3
"""
Test 09: Manual KiCad position changes survive Python regeneration.

Tests THE CRITICAL WORKFLOW: Manual edits in KiCad preserved when regenerating from Python.

This is the killer feature - if users lose manual layout work when they add
a component in Python and regenerate, the tool is unusable.

Steps:
1. Generate KiCad from Python
2. Manually edit KiCad schematic (simulated by directly editing .kicad_sch)
3. Import back to Python
4. Add a new component in Python
5. Regenerate KiCad
6. Verify: Manual edits from step 2 are PRESERVED

Does NOT test: Initial position setting (that's test 12)
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
    get_test_output_dir,
    print_test_header,
    print_test_footer,
)


def extract_component_position(sch_content: str, ref: str) -> tuple:
    """Extract position (x, y, rotation) for a component reference."""
    pattern = rf'\(symbol[^)]*?\(lib_id[^)]*?\).*?\(at\s+([\d.]+)\s+([\d.]+)\s+(\d+)\).*?\(property\s+"Reference"\s+"{ref}"'
    match = re.search(pattern, sch_content, re.DOTALL)
    if match:
        x, y, rotation = match.groups()
        return (float(x), float(y), int(rotation))
    return None


def test_manual_position_preservation():
    """
    Test: Manual KiCad position changes survive Python regeneration.

    This is THE critical test for real-world usability.
    """
    print_test_header("09: Manual Position Preservation (CRITICAL)")

    # Setup
    test_file = Path(__file__)
    output_dir = get_test_output_dir(test_file, "09_manual_position")
    clean_output_dir(output_dir)

    # Step 1: Generate initial KiCad from Python
    print("Step 1: Generating initial KiCad circuit...")
    fixture = Path(__file__).parent / "single_resistor.py"
    circuit_file = copy_to_output(fixture, output_dir, "step1_initial.py")

    exit_code, stdout, stderr = run_python_circuit(circuit_file)
    if exit_code != 0:
        print(f"❌ Initial generation failed: {stderr}")
        print_test_footer(success=False)
        assert False, f"Generation failed: {stderr}"

    kicad_dir = output_dir / "single_resistor"
    kicad_pro = assert_kicad_project_exists(kicad_dir, "single_resistor")
    kicad_sch = kicad_dir / "single_resistor.kicad_sch"
    print(f"✅ Initial KiCad generated")

    # Get original position
    sch_content = kicad_sch.read_text()
    original_pos = extract_component_position(sch_content, "R1")
    print(f"   R1 original position: {original_pos}")

    # Step 2: Simulate manual edit - move R1 to a specific position
    print("\nStep 2: Simulating manual KiCad edit (moving R1)...")
    # We'll manually set R1 to position (100.0, 200.0, 45°)
    # In real workflow, user would drag component in KiCad GUI
    manual_x, manual_y, manual_rot = 100.0, 200.0, 45

    # Find and replace R1's position in the schematic
    # Pattern to find R1's position line
    old_pattern = rf'(\(symbol[^)]*?\(lib_id[^)]*?\))(\s*\(at\s+[\d.]+\s+[\d.]+\s+\d+\))([^)]*?\(property\s+"Reference"\s+"R1")'

    def replace_position(match):
        before = match.group(1)
        after = match.group(3)
        new_at = f'\n    (at {manual_x} {manual_y} {manual_rot})'
        return before + new_at + after

    sch_content = re.sub(old_pattern, replace_position, sch_content, flags=re.DOTALL)
    kicad_sch.write_text(sch_content)

    # Verify manual edit worked
    edited_pos = extract_component_position(kicad_sch.read_text(), "R1")
    print(f"   R1 manually moved to: {edited_pos}")

    if edited_pos != (manual_x, manual_y, manual_rot):
        print(f"   ⚠️  Manual edit simulation failed")
    else:
        print(f"   ✅ Manual position applied")

    # Step 3: Import back to Python
    print("\nStep 3: Importing KiCad back to Python...")
    imported_py = output_dir / "step3_imported.py"
    exit_code, stdout, stderr = import_kicad_to_python(kicad_pro, imported_py)

    if exit_code != 0:
        print(f"❌ Import failed: {stderr}")
        print_test_footer(success=False)
        assert False, f"Import failed: {stderr}"

    print(f"✅ Imported to: {imported_py}")

    # Step 4: Modify Python (add R2) and regenerate
    print("\nStep 4: Adding R2 in Python and regenerating KiCad...")

    # Read imported Python and add R2
    py_content = imported_py.read_text()

    # Find the R1 component and add R2 after it
    r1_component = 'r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")'

    if r1_component in py_content:
        r2_addition = '''r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")

    # Added component
    r2 = Component(symbol="Device:R", ref="R2", value="20k", footprint="Resistor_SMD:R_0603_1608Metric")'''

        py_content = py_content.replace(r1_component, r2_addition)
        imported_py.write_text(py_content)
        print("   ✅ Added R2 to Python circuit")
    else:
        print("   ⚠️  Could not find R1 component in imported Python")

    # Regenerate KiCad
    exit_code, stdout, stderr = run_python_circuit(imported_py)

    if exit_code != 0:
        print(f"❌ Regeneration failed: {stderr}")
        print_test_footer(success=False)
        assert False, f"Regeneration failed: {stderr}"

    print(f"✅ KiCad regenerated with R2")

    # Step 5: Check if manual position was preserved
    print("\nStep 5: Verifying manual position preserved...")
    final_sch_content = kicad_sch.read_text()
    final_r1_pos = extract_component_position(final_sch_content, "R1")
    final_r2_pos = extract_component_position(final_sch_content, "R2")

    print(f"   R1 final position: {final_r1_pos}")
    print(f"   R2 position: {final_r2_pos}")

    # Check if R1 position matches manual edit
    if final_r1_pos:
        x_match = abs(final_r1_pos[0] - manual_x) < 0.1
        y_match = abs(final_r1_pos[1] - manual_y) < 0.1
        rot_match = final_r1_pos[2] == manual_rot

        if x_match and y_match and rot_match:
            print("   ✅ MANUAL POSITION PRESERVED!")
            print(f"      Manual edit: ({manual_x}, {manual_y}, {manual_rot}°)")
            print(f"      After regen:  {final_r1_pos}")
            success = True
        else:
            print("   ❌ MANUAL POSITION LOST!")
            print(f"      Manual edit: ({manual_x}, {manual_y}, {manual_rot}°)")
            print(f"      After regen:  {final_r1_pos}")
            print("      This is CRITICAL - users will lose layout work!")
            success = False
    else:
        print("   ❌ R1 not found after regeneration")
        success = False

    # Summary
    print("\n📊 Manual Position Preservation Test:")
    print("-" * 60)
    print(f"Original position:    {original_pos}")
    print(f"Manually edited to:   ({manual_x}, {manual_y}, {manual_rot}°)")
    print(f"After Python regen:   {final_r1_pos}")
    print(f"R2 added at:          {final_r2_pos}")
    print()
    if success:
        print("Result: ✅ MANUAL EDITS PRESERVED (Tool is usable!)")
    else:
        print("Result: ❌ MANUAL EDITS LOST (CRITICAL ISSUE)")
    print("-" * 60)

    print_test_footer(success=success)
    if not success:
        assert False, "Manual position preservation failed"


if __name__ == "__main__":
    test_manual_position_preservation()
