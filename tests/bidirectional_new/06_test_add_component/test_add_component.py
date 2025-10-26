#!/usr/bin/env python3
"""
Test 06: Add component to existing circuit.

Tests ONLY: Adding a new component
- Starts with circuit containing R1
- Adds R2 in Python
- Regenerates KiCad
- Verifies both R1 and R2 exist in KiCad

Does NOT test: Delete, modify, connections
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


def test_add_component():
    """
    Test: Adding component in Python appears in KiCad.

    Steps:
    1. Start with single_resistor.py (has R1)
    2. Modify to add R2
    3. Generate KiCad
    4. Verify both R1 and R2 in schematic

    Expected: Both components present in KiCad
    """
    print_test_header("06: Add Component")

    # Setup
    test_file = Path(__file__)
    output_dir = get_test_output_dir(test_file, "06_add_component")
    clean_output_dir(output_dir)

    # Get fixture and copy to output
    fixture = Path(__file__).parent.parent / "fixtures" / "single_resistor.py"
    circuit_file = copy_to_output(fixture, output_dir, "circuit_with_add.py")

    # Step 1: Modify circuit to add R2
    print("Step 1: Modifying circuit to add R2...")
    content = circuit_file.read_text()

    # Find the R1 component definition and add R2 after it
    # Look for the component creation line
    original_component = '''    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )'''

    new_components = '''    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Added component: R2
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="20k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )'''

    content = content.replace(original_component, new_components)
    circuit_file.write_text(content)
    print("✅ Added R2 to circuit")

    # Step 2: Generate KiCad
    print("\nStep 2: Generating KiCad...")
    exit_code, stdout, stderr = run_python_circuit(circuit_file)

    if exit_code != 0:
        print(f"❌ Generation failed: {stderr}")
        print_test_footer(success=False)
        assert False, f"Generation failed: {stderr}"

    kicad_dir = output_dir / "single_resistor"
    kicad_pro = assert_kicad_project_exists(kicad_dir, "single_resistor")
    print(f"✅ KiCad generated: {kicad_pro}")

    # Step 3: Verify both components in schematic
    print("\nStep 3: Verifying components in schematic...")
    kicad_sch = kicad_dir / "single_resistor.kicad_sch"

    assert_component_in_schematic(kicad_sch, "R1")
    print("  ✅ R1 found")

    assert_component_in_schematic(kicad_sch, "R2")
    print("  ✅ R2 found (newly added)")

    # Summary
    print("\n📊 Component Addition Summary:")
    print("-" * 60)
    print("Original circuit: 1 component (R1)")
    print("Modified circuit: 2 components (R1, R2)")
    print("KiCad schematic: Both components present ✅")
    print("-" * 60)

    print_test_footer(success=True)


if __name__ == "__main__":
    test_add_component()
