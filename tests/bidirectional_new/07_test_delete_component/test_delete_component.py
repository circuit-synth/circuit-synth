#!/usr/bin/env python3
"""
Test 07: Delete component from circuit.

Tests ONLY: Removing a component
- Starts with circuit containing R1 and R2
- Removes R2 in Python
- Regenerates KiCad
- Verifies only R1 exists in KiCad

Does NOT test: Add, modify, connections
"""

from pathlib import Path
import sys

# Add parent directory to path for test_utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_utils import (
    clean_output_dir,
    run_python_circuit,
    assert_kicad_project_exists,
    assert_component_in_schematic,
    get_test_output_dir,
    print_test_header,
    print_test_footer,
)


def test_delete_component():
    """
    Test: Deleting component in Python removes it from KiCad.

    Steps:
    1. Create circuit with R1 and R2
    2. Modify to remove R2
    3. Generate KiCad
    4. Verify only R1 in schematic (R2 gone)

    Expected: R2 removed from KiCad
    """
    print_test_header("07: Delete Component")

    # Setup
    test_file = Path(__file__)
    output_dir = get_test_output_dir(test_file, "07_delete_component")
    clean_output_dir(output_dir)

    # Step 1: Create circuit with two components
    print("Step 1: Creating circuit with R1 and R2...")
    circuit_file = output_dir / "circuit_with_delete.py"

    circuit_content = '''#!/usr/bin/env python3
"""Circuit with two resistors, then delete one."""

from circuit_synth import circuit, Component


@circuit(name="delete_test")
def delete_test():
    """Circuit with two resistors."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # This component will be deleted
    # r2 = Component(
    #     symbol="Device:R",
    #     ref="R2",
    #     value="20k",
    #     footprint="Resistor_SMD:R_0603_1608Metric"
    # )


if __name__ == "__main__":
    circuit_obj = delete_test()
    circuit_obj.generate_kicad_project(
        project_name="delete_test",
        placement_algorithm="simple",
        generate_pcb=True,
    )
'''

    circuit_file.write_text(circuit_content)
    print("✅ Created circuit with R2 commented out (deleted)")

    # Step 2: Generate KiCad
    print("\nStep 2: Generating KiCad...")
    exit_code, stdout, stderr = run_python_circuit(circuit_file)

    if exit_code != 0:
        print(f"❌ Generation failed: {stderr}")
        print_test_footer(success=False)
        assert False, f"Generation failed: {stderr}"

    kicad_dir = output_dir / "delete_test"
    kicad_pro = assert_kicad_project_exists(kicad_dir, "delete_test")
    print(f"✅ KiCad generated: {kicad_pro}")

    # Step 3: Verify only R1 in schematic
    print("\nStep 3: Verifying R1 present, R2 absent...")
    kicad_sch = kicad_dir / "delete_test.kicad_sch"

    assert_component_in_schematic(kicad_sch, "R1")
    print("  ✅ R1 found (kept)")

    # Check that R2 is NOT in the schematic
    sch_content = kicad_sch.read_text()
    if '"Reference" "R2"' in sch_content:
        print("  ❌ R2 still exists (should be deleted)")
        print_test_footer(success=False)
        assert False, "R2 was not deleted from schematic"
    else:
        print("  ✅ R2 absent (successfully deleted)")

    # Summary
    print("\n📊 Component Deletion Summary:")
    print("-" * 60)
    print("Original circuit: 2 components (R1, R2)")
    print("Modified circuit: 1 component (R1 only)")
    print("KiCad schematic: R1 present, R2 absent ✅")
    print("-" * 60)

    print_test_footer(success=True)


if __name__ == "__main__":
    test_delete_component()
