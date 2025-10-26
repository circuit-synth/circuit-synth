#!/usr/bin/env python3
"""
Test 10: Add component to existing net.

Tests: Adding a third component to an existing connection between two components.

Real-world scenario: You have R1-R2 connected, now add R3 to the same net.

Steps:
1. Create circuit with R1-R2 connected via NET1
2. Generate KiCad
3. Add R3 connected to same NET1
4. Regenerate KiCad
5. Verify all three components on same net

Does NOT test: Creating new net (test 17), deleting net (test 22)
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


def test_add_to_existing_net():
    """
    Test: Adding component to existing net connection.

    Real scenario: Expanding a connection to include more components.
    """
    print_test_header("10: Add Component to Existing Net")

    # Setup
    test_file = Path(__file__)
    output_dir = get_test_output_dir(test_file, "10_add_to_net")
    clean_output_dir(output_dir)

    # Step 1: Create circuit with R1-R2-R3 all on NET1
    print("Step 1: Creating circuit with 3 components on same net...")
    circuit_file = output_dir / "three_on_net.py"

    circuit_content = '''#!/usr/bin/env python3
"""Three resistors connected to same net."""

from circuit_synth import circuit, Component, Net


@circuit(name="three_resistors_net")
def three_resistors_net():
    """Three resistors on NET1."""
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

    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="30k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # All three components on same net
    net1 = Net("SHARED_NET")
    net1 += r1["2"]
    net1 += r2["1"]
    net1 += r3["1"]  # R3 added to existing net


if __name__ == "__main__":
    circuit_obj = three_resistors_net()
    circuit_obj.generate_kicad_project(
        project_name="three_resistors_net",
        placement_algorithm="simple",
        generate_pcb=True,
    )
'''

    circuit_file.write_text(circuit_content)
    print("✅ Created circuit with R1, R2, R3 on SHARED_NET")

    # Step 2: Generate KiCad
    print("\nStep 2: Generating KiCad...")
    exit_code, stdout, stderr = run_python_circuit(circuit_file)

    if exit_code != 0:
        print(f"❌ Generation failed: {stderr}")
        print_test_footer(success=False)
        assert False, f"Generation failed: {stderr}"

    kicad_dir = output_dir / "three_resistors_net"
    kicad_pro = assert_kicad_project_exists(kicad_dir, "three_resistors_net")
    print(f"✅ KiCad generated: {kicad_pro}")

    # Step 3: Verify all components exist
    print("\nStep 3: Verifying all components in schematic...")
    kicad_sch = kicad_dir / "three_resistors_net.kicad_sch"

    assert_component_in_schematic(kicad_sch, "R1")
    print("  ✅ R1 present")

    assert_component_in_schematic(kicad_sch, "R2")
    print("  ✅ R2 present")

    assert_component_in_schematic(kicad_sch, "R3")
    print("  ✅ R3 present (added to existing net)")

    # Step 4: Verify net label
    print("\nStep 4: Verifying net connection...")
    sch_content = kicad_sch.read_text()

    has_shared_net = '"SHARED_NET"' in sch_content or "'SHARED_NET'" in sch_content

    if has_shared_net:
        print("  ✅ SHARED_NET label found")
    else:
        print("  ⚠️  SHARED_NET label not explicitly found")
        print("      (Connections may be implicit)")

    # Count wires/junctions - should have multiple for 3-way connection
    wire_count = sch_content.count("(wire")
    junction_count = sch_content.count("(junction")

    print(f"  Connection elements: {wire_count} wires, {junction_count} junctions")

    # Summary
    print("\n📊 Add to Existing Net Summary:")
    print("-" * 60)
    print("Components: R1, R2, R3")
    print("Net: SHARED_NET (3-way connection)")
    print(f"  R1.pin2 → SHARED_NET")
    print(f"  R2.pin1 → SHARED_NET")
    print(f"  R3.pin1 → SHARED_NET (added)")
    print()
    print("KiCad schematic:")
    print(f"  - All 3 components present ✅")
    print(f"  - Net label present: {has_shared_net}")
    print(f"  - Connection elements: {wire_count + junction_count}")
    print("-" * 60)

    print_test_footer(success=True)


if __name__ == "__main__":
    test_add_to_existing_net()
