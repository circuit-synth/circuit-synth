#!/usr/bin/env python3
"""
Test 05: Simple round-trip cycle works.

Tests ONLY: Complete cycle (Python → KiCad → Python → KiCad)
- Generates KiCad from Python
- Imports back to Python
- Generates KiCad again from imported Python
- Verifies both KiCad projects contain same component

Does NOT test: Detailed property comparison, modifications, positions
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
    assert_component_in_schematic,
    get_test_output_dir,
    print_test_header,
    print_test_footer,
)


def test_roundtrip():
    """
    Test: Complete round-trip cycle preserves circuit.

    Steps:
    1. Generate KiCad from fixture (original)
    2. Import to Python
    3. Generate KiCad from imported Python (roundtrip)
    4. Assert both KiCad projects contain R1

    Expected: Component exists in both original and roundtrip KiCad
    """
    print_test_header("05: Simple Round-Trip Cycle")

    # Setup - use shared generated/ directory
    test_file = Path(__file__)
    output_dir = get_test_output_dir(test_file, "05_roundtrip")
    clean_output_dir(output_dir)

    # Get fixture
    fixture = Path(__file__).parent / "single_resistor.py"
    original_py = copy_to_output(fixture, output_dir, "step1_original.py")

    # Step 1: Generate original KiCad
    print("Step 1: Generating original KiCad...")
    exit_code, stdout, stderr = run_python_circuit(original_py)

    if exit_code != 0:
        print(f"❌ Original generation failed: {stderr}")
        print_test_footer(success=False)
        assert False, f"Generation failed: {stderr}"

    original_kicad = output_dir / "single_resistor"
    original_pro = assert_kicad_project_exists(original_kicad, "single_resistor")
    print(f"✅ Original KiCad: {original_pro}")

    # Step 2: Import to Python
    print("\nStep 2: Importing to Python...")
    imported_py = output_dir / "step2_imported.py"
    exit_code, stdout, stderr = import_kicad_to_python(original_pro, imported_py)

    if exit_code != 0:
        print(f"❌ Import failed: {stderr}")
        print_test_footer(success=False)
        assert False, f"Import failed: {stderr}"

    print(f"✅ Imported Python: {imported_py}")

    # Step 3: Generate roundtrip KiCad
    print("\nStep 3: Generating roundtrip KiCad...")

    # Modify the imported Python to use different project name
    content = imported_py.read_text()
    # Replace project name to avoid overwriting
    content = content.replace('project_name="single_resistor_generated"', 'project_name="roundtrip_resistor"')
    imported_py.write_text(content)

    exit_code, stdout, stderr = run_python_circuit(imported_py)

    if exit_code != 0:
        print(f"❌ Roundtrip generation failed: {stderr}")
        print_test_footer(success=False)
        assert False, f"Roundtrip generation failed: {stderr}"

    roundtrip_kicad = output_dir / "roundtrip_resistor"
    roundtrip_pro = assert_kicad_project_exists(roundtrip_kicad, "roundtrip_resistor")
    print(f"✅ Roundtrip KiCad: {roundtrip_pro}")

    # Step 4: Verify both contain R1
    print("\nStep 4: Verifying component in both projects...")

    original_sch = original_kicad / "single_resistor.kicad_sch"
    assert_component_in_schematic(original_sch, "R1")
    print("  ✅ R1 in original schematic")

    roundtrip_sch = roundtrip_kicad / "roundtrip_resistor.kicad_sch"
    assert_component_in_schematic(roundtrip_sch, "R1")
    print("  ✅ R1 in roundtrip schematic")

    # Summary
    print("\n📊 Round-Trip Summary:")
    print("-" * 60)
    print(f"Original:  {original_py.name} → {original_kicad.name}")
    print(f"Imported:  {original_kicad.name} → {imported_py.name}")
    print(f"Roundtrip: {imported_py.name} → {roundtrip_kicad.name}")
    print(f"")
    print(f"Result: Component R1 present in all stages ✅")
    print("-" * 60)

    # Success
    print_test_footer(success=True)


if __name__ == "__main__":
    test_roundtrip()
