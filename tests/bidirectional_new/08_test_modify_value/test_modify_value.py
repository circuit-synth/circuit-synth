#!/usr/bin/env python3
"""
Test 08: Modify component value.

Tests ONLY: Changing component value
- Starts with R1=10k
- Changes to R1=20k
- Regenerates KiCad
- Verifies new value in KiCad and round-trip

Does NOT test: Add, delete, footprint changes
"""

from pathlib import Path
import sys

# Add parent directory to path for test_utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_utils import (
    clean_output_dir,
    copy_to_output,
    run_python_circuit,
    import_kicad_to_python,
    assert_kicad_project_exists,
    assert_component_properties,
    get_test_output_dir,
    print_test_header,
    print_test_footer,
)


def test_modify_value():
    """
    Test: Modifying component value propagates to KiCad.

    Steps:
    1. Start with R1=10k
    2. Modify to R1=20k
    3. Generate KiCad
    4. Import back to Python
    5. Verify value=20k in both KiCad and reimported Python

    Expected: Value change preserved through cycle
    """
    print_test_header("08: Modify Component Value")

    # Setup
    test_file = Path(__file__)
    output_dir = get_test_output_dir(test_file, "08_modify_value")
    clean_output_dir(output_dir)

    # Get fixture and copy
    fixture = Path(__file__).parent / "single_resistor.py"
    circuit_file = copy_to_output(fixture, output_dir, "circuit_modified.py")

    # Step 1: Modify value from 10k to 20k
    print("Step 1: Modifying R1 value from 10k to 20k...")
    content = circuit_file.read_text()
    content = content.replace('value="10k"', 'value="20k"')
    circuit_file.write_text(content)
    print("✅ Modified value in Python")

    # Step 2: Generate KiCad
    print("\nStep 2: Generating KiCad with modified value...")
    exit_code, stdout, stderr = run_python_circuit(circuit_file)

    if exit_code != 0:
        print(f"❌ Generation failed: {stderr}")
        print_test_footer(success=False)
        assert False, f"Generation failed: {stderr}"

    kicad_dir = output_dir / "single_resistor"
    kicad_pro = assert_kicad_project_exists(kicad_dir, "single_resistor")
    print(f"✅ KiCad generated: {kicad_pro}")

    # Step 3: Verify value in KiCad schematic
    print("\nStep 3: Verifying value in KiCad schematic...")
    kicad_sch = kicad_dir / "single_resistor.kicad_sch"
    sch_content = kicad_sch.read_text()

    if '"Value" "20k"' in sch_content:
        print("  ✅ Value '20k' found in KiCad schematic")
    else:
        print("  ❌ Value '20k' not found in schematic")
        print_test_footer(success=False)
        assert False, "Modified value not in KiCad schematic"

    # Step 4: Import back to Python
    print("\nStep 4: Importing back to Python...")
    imported_py = output_dir / "imported_modified.py"
    exit_code, stdout, stderr = import_kicad_to_python(kicad_pro, imported_py)

    if exit_code != 0:
        print(f"❌ Import failed: {stderr}")
        print_test_footer(success=False)
        assert False, f"Import failed: {stderr}"

    print(f"✅ Imported to Python: {imported_py}")

    # Step 5: Verify modified value in imported Python
    print("\nStep 5: Verifying value in imported Python...")
    assert_component_properties(imported_py, reference="R1", value="20k")
    print("  ✅ Value '20k' preserved in round-trip")

    # Summary
    print("\n📊 Value Modification Summary:")
    print("-" * 60)
    print("Original value:  10k")
    print("Modified value:  20k")
    print("KiCad schematic: 20k ✅")
    print("Reimported:      20k ✅")
    print("Result: Value change preserved ✅")
    print("-" * 60)

    print_test_footer(success=True)


if __name__ == "__main__":
    test_modify_value()
