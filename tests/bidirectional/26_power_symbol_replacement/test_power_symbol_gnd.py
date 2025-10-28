#!/usr/bin/env python3
"""
Unit test for GND power symbol generation.
Compares generated schematic against manually corrected reference.
"""

from circuit_synth import circuit, Component, Net

@circuit(name="test_power_symbol_gnd")
def test_power_symbol_gnd():
    """Test circuit: Single resistor connected to GND."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Connect to GND (pin 2 - bottom pin)
    gnd = Net(name="GND")
    gnd += r1[2]

if __name__ == "__main__":
    import subprocess
    import sys

    # Generate the test schematic
    circuit_obj = test_power_symbol_gnd()
    circuit_obj.generate_kicad_project(project_name="test_power_symbol_gnd")

    print("\n" + "="*70)
    print("TEST: GND Power Symbol")
    print("="*70)

    # Compare with reference
    print("\n📊 Comparing with reference...")

    # Extract power symbol position from generated schematic
    with open("test_power_symbol_gnd/test_power_symbol_gnd.kicad_sch", "r") as f:
        content = f.read()

    # Find power symbol
    import re
    power_match = re.search(r'\(lib_id "power:GND"\)\s+\(at ([\d.]+) ([\d.]+) ([\d.]+)\)', content)

    if power_match:
        gen_x, gen_y, gen_rot = power_match.groups()
        print(f"Generated:  power:GND at ({gen_x}, {gen_y}, {gen_rot}°)")
        print(f"Expected:   power:GND at (30.48, 39.37, 180°)")

        # Check if positions match
        # Note: GND symbols now correctly point downward (180°) based on pin orientation
        if gen_x == "30.48" and gen_y == "39.37" and gen_rot == "180":
            print("\n✅ TEST PASSED: Power symbol position matches reference!")
            sys.exit(0)
        else:
            print("\n❌ TEST FAILED: Power symbol position does not match!")
            print(f"   Difference: x={float(gen_x)-30.48:.2f}, y={float(gen_y)-39.37:.2f}, rot={float(gen_rot)-180:.0f}")
            sys.exit(1)
    else:
        print("\n❌ TEST FAILED: No GND power symbol found in generated schematic!")
        sys.exit(1)
