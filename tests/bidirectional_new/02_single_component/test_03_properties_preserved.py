#!/usr/bin/env python3
"""
Test: Component properties preserved through generation and import.

Tests ONLY: Property preservation (reference, value, footprint)
- Generates KiCad from Python
- Imports back to Python
- Verifies properties match original

Does NOT test: Position, connections, modifications
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


def test_properties_preserved():
    """
    Test: Component properties survive Python → KiCad → Python.

    Steps:
    1. Generate KiCad from fixture (R1: 10k, R_0603)
    2. Import back to Python
    3. Assert properties match: ref="R1", value="10k", footprint contains "0603"

    Expected: All properties preserved exactly
    """
    print_test_header("Component Properties Preserved")

    # Setup
    test_file = Path(__file__)
    output_dir = get_test_output_dir(test_file, "properties")
    clean_output_dir(output_dir)

    # Get fixture
    fixture = Path(__file__).parent.parent / "fixtures" / "single_resistor.py"
    circuit_file = copy_to_output(fixture, output_dir, "original_circuit.py")

    # Step 1: Generate KiCad from Python
    print("Step 1: Generating KiCad from Python...")
    exit_code, stdout, stderr = run_python_circuit(circuit_file)

    if exit_code != 0:
        print(f"❌ Generation failed: {stderr}")
        print_test_footer(success=False)
        assert False, f"Generation failed: {stderr}"

    kicad_dir = output_dir / "single_resistor"
    kicad_pro = assert_kicad_project_exists(kicad_dir, "single_resistor")
    print(f"✅ KiCad project generated: {kicad_pro}")

    # Step 2: Import back to Python
    print("\nStep 2: Importing back to Python...")
    imported_py = output_dir / "imported_circuit.py"
    exit_code, stdout, stderr = import_kicad_to_python(kicad_pro, imported_py)

    if exit_code != 0:
        print(f"❌ Import failed: {stderr}")
        print_test_footer(success=False)
        assert False, f"Import failed: {stderr}"

    print(f"✅ Imported to Python: {imported_py}")

    # Step 3: Verify properties preserved
    print("\nStep 3: Verifying properties...")

    # Check reference
    print("  Checking reference='R1'...")
    assert_component_properties(imported_py, reference="R1")
    print("  ✅ Reference preserved")

    # Check value
    print("  Checking value='10k'...")
    assert_component_properties(imported_py, reference="R1", value="10k")
    print("  ✅ Value preserved")

    # Check footprint (partial match - just verify it contains the size)
    print("  Checking footprint contains '0603'...")
    assert_component_properties(imported_py, reference="R1", footprint="0603")
    print("  ✅ Footprint preserved")

    # Show comparison
    print("\n📊 Property Comparison:")
    print("-" * 60)
    print("Original properties:")
    print("  reference: R1")
    print("  value: 10k")
    print("  footprint: Resistor_SMD:R_0603_1608Metric")
    print()
    print("Imported properties:")
    content = imported_py.read_text()
    # Extract the Component line for R1
    for line in content.split('\n'):
        if 'ref="R1"' in line or "ref='R1'" in line:
            print(f"  {line.strip()}")
    print("-" * 60)

    # Success
    print(f"\n✅ All properties preserved correctly!")
    print_test_footer(success=True)


if __name__ == "__main__":
    test_properties_preserved()
