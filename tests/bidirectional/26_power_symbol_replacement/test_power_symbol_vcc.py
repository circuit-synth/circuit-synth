#!/usr/bin/env python3
"""
Unit test for VCC power symbol generation.
Compares generated schematic against manually corrected reference.
"""

from circuit_synth import circuit, Component, Net

@circuit(name="test_power_symbol_vcc")
def test_power_symbol_vcc():
    """Test circuit: Single resistor connected to VCC."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Connect to VCC (pin 1 - top pin)
    vcc = Net(name="VCC")
    vcc += r1[1]

if __name__ == "__main__":
    import subprocess
    import sys

    # Generate the test schematic
    circuit_obj = test_power_symbol_vcc()
    circuit_obj.generate_kicad_project(project_name="test_power_symbol_vcc")

    print("\n" + "="*70)
    print("TEST: VCC Power Symbol")
    print("="*70)

    # Compare with reference
    print("\n📊 Comparing with reference...")

    # Extract power symbol position from generated schematic
    with open("test_power_symbol_vcc/test_power_symbol_vcc.kicad_sch", "r") as f:
        content = f.read()

    # Find power symbol
    import re
    power_match = re.search(r'\(lib_id "power:VCC"\)\s+\(at ([\d.]+) ([\d.]+) ([\d.]+)\)', content)

    if power_match:
        gen_x, gen_y, gen_rot = power_match.groups()
        print(f"Generated:  power:VCC at ({gen_x}, {gen_y}, {gen_rot}°)")
        print(f"Expected:   power:VCC at (30.48, 31.75, 0°)")

        # Check if positions match
        if gen_x == "30.48" and gen_y == "31.75" and gen_rot == "0":
            print("\n✅ TEST PASSED: Power symbol position matches reference!")
            sys.exit(0)
        else:
            print("\n❌ TEST FAILED: Power symbol position does not match!")
            print(f"   Difference: x={float(gen_x)-30.48:.2f}, y={float(gen_y)-31.75:.2f}, rot={float(gen_rot)-0:.0f}")
            sys.exit(1)
    else:
        print("\n❌ TEST FAILED: No VCC power symbol found in generated schematic!")
        sys.exit(1)
