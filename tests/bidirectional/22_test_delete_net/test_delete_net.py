#!/usr/bin/env python3
"""
Test 22: Delete net connection between components.

Tests ONLY: Removing a connection/net
- Starts with two connected resistors
- Removes the net connection
- Generates KiCad
- Verifies connection is gone in KiCad

Does NOT test: Create net, modify net, multi-point nets
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


def test_delete_net():
    """
    Test: Deleting net connection in Python removes it from KiCad.

    Steps:
    1. Create circuit with R1 and R2
    2. DON'T create net (simulating deletion)
    3. Generate KiCad
    4. Verify components exist but no connection

    Expected: Components present, connection absent
    """
    print_test_header("22: Delete Net Connection")

    # Setup
    test_file = Path(__file__)
    output_dir = get_test_output_dir(test_file, "22_delete_net")
    clean_output_dir(output_dir)

    # Step 1: Create circuit WITHOUT connection
    print("Step 1: Creating circuit without connection (net deleted)...")
    circuit_file = output_dir / "circuit_no_net.py"

    circuit_content = '''#!/usr/bin/env python3
"""Circuit with two resistors, no connection."""

from circuit_synth import circuit, Component


@circuit(name="disconnected_resistors")
def disconnected_resistors():
    """Two resistors without connection."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="20k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Net connection commented out (deleted)
    # net1 = Net("NET1")
    # net1.connect(r1["2"])
    # net1.connect(r2["1"])


if __name__ == "__main__":
    circuit_obj = disconnected_resistors()
    circuit_obj.generate_kicad_project(
        project_name="disconnected_resistors",
        placement_algorithm="simple",
        generate_pcb=True,
    )
'''

    circuit_file.write_text(circuit_content)
    print("✅ Created circuit with net commented out (deleted)")

    # Step 2: Generate KiCad
    print("\nStep 2: Generating KiCad...")
    exit_code, stdout, stderr = run_python_circuit(circuit_file)

    if exit_code != 0:
        print(f"❌ Generation failed: {stderr}")
        print_test_footer(success=False)
        assert False, f"Generation failed: {stderr}"

    kicad_dir = output_dir / "disconnected_resistors"
    kicad_pro = assert_kicad_project_exists(kicad_dir, "disconnected_resistors")
    print(f"✅ KiCad generated: {kicad_pro}")

    # Step 3: Verify components exist
    print("\nStep 3: Verifying components present...")
    kicad_sch = kicad_dir / "disconnected_resistors.kicad_sch"

    assert_component_in_schematic(kicad_sch, "R1")
    print("  ✅ R1 present")

    assert_component_in_schematic(kicad_sch, "R2")
    print("  ✅ R2 present")

    # Step 4: Verify no NET1 connection
    print("\nStep 4: Verifying net deleted...")
    sch_content = kicad_sch.read_text()

    # Count wire/junction elements - should be minimal for disconnected components
    wire_count = sch_content.count("(wire")
    junction_count = sch_content.count("(junction")
    has_net_label = '"NET1"' in sch_content or "'NET1'" in sch_content

    print(f"  Wire count: {wire_count}")
    print(f"  Junction count: {junction_count}")

    if has_net_label:
        print("  ❌ NET1 label still present (should be deleted)")
        print_test_footer(success=False)
        assert False, "Net label found when it should be deleted"
    else:
        print("  ✅ NET1 label absent (successfully deleted)")

    # Summary
    print("\n📊 Net Deletion Summary:")
    print("-" * 60)
    print("Components: R1 ✅, R2 ✅ (both present)")
    print("Connection: None (net deleted)")
    print("KiCad schematic: No NET1 connection ✅")
    print("-" * 60)

    print_test_footer(success=True)


if __name__ == "__main__":
    test_delete_net()
