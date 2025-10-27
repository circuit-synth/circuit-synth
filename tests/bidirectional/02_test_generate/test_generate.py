#!/usr/bin/env python3
"""
Test 02: Generate KiCad from Python circuit.

Tests ONLY: Python → KiCad generation
- Creates single resistor circuit in Python
- Generates KiCad project
- Verifies KiCad files exist and contain the component

Does NOT test: Import, round-trip, property preservation
"""

from pathlib import Path
import sys

# Add parent directory to path for test_utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_utils import (
    clean_output_dir,
    copy_to_output,
    run_python_circuit,
    assert_kicad_project_exists,
    assert_component_in_schematic,
    get_test_output_dir,
    print_test_header,
    print_test_footer,
)


def test_generate():
    """
    Test: Python → KiCad generation with single resistor.

    Steps:
    1. Copy fixture circuit to output directory
    2. Run the Python circuit file
    3. Assert KiCad project was created
    4. Assert R1 component exists in schematic

    Expected: KiCad project generated with R1 resistor
    """
    print_test_header("02: Generate KiCad from Python")

    # Setup - use shared generated/ directory
    test_file = Path(__file__)
    output_dir = get_test_output_dir(test_file, "02_generate")
    clean_output_dir(output_dir)

    # Get fixture from same directory
    fixture = Path(__file__).parent / "single_resistor.py"
    circuit_file = copy_to_output(fixture, output_dir)

    # Step 1: Run Python circuit to generate KiCad
    print("Step 1: Running Python circuit...")
    exit_code, stdout, stderr = run_python_circuit(circuit_file)

    if exit_code != 0:
        print(f"❌ Generation failed with exit code {exit_code}")
        print(f"STDERR: {stderr}")
        print_test_footer(success=False)
        assert False, f"Circuit generation failed: {stderr}"

    print(f"✅ Generation completed (exit code: {exit_code})")

    # Step 2: Verify KiCad project exists
    print("\nStep 2: Verifying KiCad project...")
    kicad_dir = output_dir / "single_resistor"
    kicad_pro = assert_kicad_project_exists(kicad_dir, "single_resistor")
    print(f"✅ KiCad project found: {kicad_pro}")

    # Step 3: Verify component in schematic
    print("\nStep 3: Verifying component in schematic...")
    kicad_sch = kicad_dir / "single_resistor.kicad_sch"
    assert_component_in_schematic(kicad_sch, "R1")
    print("✅ Component R1 found in schematic")

    # Success
    print(f"\n📁 Generated project: {kicad_dir}")
    print_test_footer(success=True)


if __name__ == "__main__":
    test_generate()
