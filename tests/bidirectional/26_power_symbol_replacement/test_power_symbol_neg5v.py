#!/usr/bin/env python3
"""
Unit test for -5V power symbol generation.
Compares generated schematic against manually corrected reference.
Note: -5V symbol should be rotated 180° to point downward.
"""

from circuit_synth import circuit, Component, Net

@circuit(name="test_power_symbol_neg5v")
def test_power_symbol_neg5v():
    """Test circuit: Single resistor connected to -5V."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Connect to -5V (pin 2 - bottom pin)
    neg5v = Net(name="-5V")
    neg5v += r1[2]

if __name__ == "__main__":
    import subprocess
    import sys

    # Generate the test schematic
    circuit_obj = test_power_symbol_neg5v()
    circuit_obj.generate_kicad_project(project_name="test_power_symbol_neg5v")

    print("\n" + "="*70)
    print("TEST: -5V Power Symbol")
    print("="*70)

    # Compare with reference
    print("\n📊 Comparing with reference...")

    # Extract power symbol position from generated schematic
    with open("test_power_symbol_neg5v/test_power_symbol_neg5v.kicad_sch", "r") as f:
        content = f.read()

    # Find power symbol
    import re
    power_match = re.search(r'\(lib_id "power:-5V"\)\s+\(at ([\d.]+) ([\d.]+) ([\d.]+)\)', content)

    if power_match:
        gen_x, gen_y, gen_rot = power_match.groups()
        print(f"Generated:  power:-5V at ({gen_x}, {gen_y}, {gen_rot}°)")
        print(f"Expected:   power:-5V at (30.48, 39.37, 180°)")

        # Check if positions match (note: 180° rotation required)
        if gen_x == "30.48" and gen_y == "39.37" and gen_rot == "180":
            print("\n✅ TEST PASSED: Power symbol position matches reference!")
            sys.exit(0)
        else:
            print("\n❌ TEST FAILED: Power symbol position does not match!")
            print(f"   Difference: x={float(gen_x)-30.48:.2f}, y={float(gen_y)-39.37:.2f}, rot={float(gen_rot)-180:.0f}")
            sys.exit(1)
    else:
        print("\n❌ TEST FAILED: No -5V power symbol found in generated schematic!")
        sys.exit(1)
