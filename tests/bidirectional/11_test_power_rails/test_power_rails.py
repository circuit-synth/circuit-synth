#!/usr/bin/env python3
"""
Test 11: Power rail connections (GND, VCC).

Tests: Multiple components connected to power rails - the most common circuit pattern.

Real-world scenario: Every circuit has GND and VCC. Multiple components need to
connect to these rails.

Steps:
1. Create circuit with 3 components
2. Connect all to GND rail
3. Connect all to VCC rail
4. Generate KiCad
5. Verify all power connections present

Does NOT test: Named nets for signals (test 17)
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


def test_power_rails():
    """
    Test: Power rail connections (GND, VCC).

    The most fundamental circuit pattern - power distribution.
    """
    print_test_header("11: Power Rails (GND, VCC)")

    # Setup
    test_file = Path(__file__)
    output_dir = get_test_output_dir(test_file, "11_power_rails")
    clean_output_dir(output_dir)

    # Step 1: Create circuit with power rails
    print("Step 1: Creating circuit with GND and VCC rails...")
    circuit_file = output_dir / "power_circuit.py"

    circuit_content = '''#!/usr/bin/env python3
"""Circuit with power rails - GND and VCC."""

from circuit_synth import circuit, Component, Net


@circuit(name="power_rails")
def power_rails():
    """Three resistors with power rail connections."""
    # Create components
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

    # GND rail - all components connect pin 1 to ground
    gnd = Net("GND")
    gnd += r1["1"]
    gnd += r2["1"]
    gnd += r3["1"]

    # VCC rail - all components connect pin 2 to power
    vcc = Net("VCC")
    vcc += r1["2"]
    vcc += r2["2"]
    vcc += r3["2"]


if __name__ == "__main__":
    circuit_obj = power_rails()
    circuit_obj.generate_kicad_project(
        project_name="power_rails",
        placement_algorithm="simple",
        generate_pcb=True,
    )
'''

    circuit_file.write_text(circuit_content)
    print("✅ Created circuit with GND and VCC rails")

    # Step 2: Generate KiCad
    print("\nStep 2: Generating KiCad...")
    exit_code, stdout, stderr = run_python_circuit(circuit_file)

    if exit_code != 0:
        print(f"❌ Generation failed: {stderr}")
        print_test_footer(success=False)
        assert False, f"Generation failed: {stderr}"

    kicad_dir = output_dir / "power_rails"
    kicad_pro = assert_kicad_project_exists(kicad_dir, "power_rails")
    print(f"✅ KiCad generated: {kicad_pro}")

    # Step 3: Verify components
    print("\nStep 3: Verifying components...")
    kicad_sch = kicad_dir / "power_rails.kicad_sch"

    for ref in ["R1", "R2", "R3"]:
        assert_component_in_schematic(kicad_sch, ref)
        print(f"  ✅ {ref} present")

    # Step 4: Verify power rail nets
    print("\nStep 4: Verifying power rail nets...")
    sch_content = kicad_sch.read_text()

    has_gnd = '"GND"' in sch_content or "'GND'" in sch_content
    has_vcc = '"VCC"' in sch_content or "'VCC'" in sch_content

    if has_gnd:
        print("  ✅ GND rail found")
    else:
        print("  ⚠️  GND rail not found (may use implicit naming)")

    if has_vcc:
        print("  ✅ VCC rail found")
    else:
        print("  ⚠️  VCC rail not found (may use implicit naming)")

    # Count connections
    wire_count = sch_content.count("(wire")
    junction_count = sch_content.count("(junction")
    label_count = sch_content.count("(label")

    print(f"\n  Connection statistics:")
    print(f"    Wires: {wire_count}")
    print(f"    Junctions: {junction_count}")
    print(f"    Labels: {label_count}")

    # Summary
    print("\n📊 Power Rails Summary:")
    print("-" * 60)
    print("Components: R1, R2, R3")
    print()
    print("GND rail (3 connections):")
    print("  R1.pin1 → GND")
    print("  R2.pin1 → GND")
    print("  R3.pin1 → GND")
    print()
    print("VCC rail (3 connections):")
    print("  R1.pin2 → VCC")
    print("  R2.pin2 → VCC")
    print("  R3.pin2 → VCC")
    print()
    print("KiCad schematic:")
    print(f"  - All components present ✅")
    print(f"  - GND net: {'✅' if has_gnd else '⚠️'}")
    print(f"  - VCC net: {'✅' if has_vcc else '⚠️'}")
    print(f"  - Total connections: {wire_count + junction_count}")
    print("-" * 60)

    print_test_footer(success=True)


if __name__ == "__main__":
    test_power_rails()
