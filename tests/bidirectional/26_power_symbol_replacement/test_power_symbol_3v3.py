#!/usr/bin/env python3
"""
Unit test for +3V3 power symbol generation.
Compares generated schematic against manually corrected reference.
"""

from circuit_synth import circuit, Component, Net

@circuit(name="test_power_symbol_3v3")
def test_power_symbol_3v3():
    """Test circuit: Single resistor connected to +3V3."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Connect to +3V3 (pin 1 - top pin)
    v3_3 = Net(name="+3V3")
    v3_3 += r1[1]

if __name__ == "__main__":
    import subprocess
    import sys

    # Generate the test schematic
    circuit_obj = test_power_symbol_3v3()
    circuit_obj.generate_kicad_project(project_name="test_power_symbol_3v3")

    print("\n" + "="*70)
    print("TEST: +3V3 Power Symbol")
    print("="*70)

    # Compare with reference
    print("\n📊 Comparing with reference...")

    # Extract power symbol position from generated schematic
    with open("test_power_symbol_3v3/test_power_symbol_3v3.kicad_sch", "r") as f:
        content = f.read()

    # Find power symbol
    import re
    power_match = re.search(r'\(lib_id "power:\+3V3"\)\s+\(at ([\d.]+) ([\d.]+) ([\d.]+)\)', content)

    if power_match:
        gen_x, gen_y, gen_rot = power_match.groups()
        print(f"Generated:  power:+3V3 at ({gen_x}, {gen_y}, {gen_rot}°)")
        print(f"Expected:   power:+3V3 at (30.48, 31.75, 0°)")

        # Check if positions match
        if gen_x == "30.48" and gen_y == "31.75" and gen_rot == "0":
            print("\n✅ TEST PASSED: Power symbol position matches reference!")
            sys.exit(0)
        else:
            print("\n❌ TEST FAILED: Power symbol position does not match!")
            print(f"   Difference: x={float(gen_x)-30.48:.2f}, y={float(gen_y)-31.75:.2f}, rot={float(gen_rot)-0:.0f}")
            sys.exit(1)
    else:
        print("\n❌ TEST FAILED: No +3V3 power symbol found in generated schematic!")
        sys.exit(1)
