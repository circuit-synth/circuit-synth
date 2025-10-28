#!/usr/bin/env python3
"""
Combined unit test for all power symbol types.
Tests GND, VCC, +3V3, +5V, and -5V in a single schematic.
Compares generated positions against manually corrected references.
"""

from circuit_synth import circuit, Component, Net

@circuit(name="test_power_symbol_all")
def test_power_symbol_all():
    """Test circuit: Multiple resistors connected to different power symbols."""

    # Create 5 resistors, one for each power symbol type
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r4 = Component(
        symbol="Device:R",
        ref="R4",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r5 = Component(
        symbol="Device:R",
        ref="R5",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Connect to different power nets
    # Positive supplies connect to top pin (1)
    vcc = Net(name="VCC")
    vcc += r1[1]

    v3_3 = Net(name="+3V3")
    v3_3 += r2[1]

    v5 = Net(name="+5V")
    v5 += r3[1]

    # Ground and negative supplies connect to bottom pin (2)
    gnd = Net(name="GND")
    gnd += r4[2]

    neg5v = Net(name="-5V")
    neg5v += r5[2]

if __name__ == "__main__":
    import subprocess
    import sys
    import re

    # Generate the test schematic
    circuit_obj = test_power_symbol_all()
    circuit_obj.generate_kicad_project(project_name="test_power_symbol_all")

    print("\n" + "="*70)
    print("TEST: All Power Symbols Combined")
    print("="*70)

    # Read generated schematic
    with open("test_power_symbol_all/test_power_symbol_all.kicad_sch", "r") as f:
        content = f.read()

    # Expected positions based on reference schematics
    expected_positions = {
        "VCC": {"x": "30.48", "y": "31.75", "rot": "0", "pin": "1"},
        "+3V3": {"x": "30.48", "y": "31.75", "rot": "0", "pin": "1"},
        "+5V": {"x": "30.48", "y": "31.75", "rot": "0", "pin": "1"},
        "GND": {"x": "30.48", "y": "39.37", "rot": "0", "pin": "2"},
        "-5V": {"x": "30.48", "y": "39.37", "rot": "180", "pin": "2"}
    }

    print("\n📊 Comparing power symbols with references...")
    all_passed = True
    results = []

    # Test each power symbol
    for power_name, expected in expected_positions.items():
        # Escape + in regex pattern
        pattern_name = power_name.replace("+", r"\+")
        power_match = re.search(
            rf'\(lib_id "power:{pattern_name}"\)\s+\(at ([\d.]+) ([\d.]+) ([\d.]+)\)',
            content
        )

        if power_match:
            gen_x, gen_y, gen_rot = power_match.groups()
            passed = (
                gen_x == expected["x"] and
                gen_y == expected["y"] and
                gen_rot == expected["rot"]
            )

            status = "✅ PASS" if passed else "❌ FAIL"
            results.append(f"{status}: {power_name:6s} at ({gen_x}, {gen_y}, {gen_rot}°) - Expected ({expected['x']}, {expected['y']}, {expected['rot']}°)")

            if not passed:
                all_passed = False
                dx = float(gen_x) - float(expected["x"])
                dy = float(gen_y) - float(expected["y"])
                drot = float(gen_rot) - float(expected["rot"])
                results.append(f"        Difference: x={dx:.2f}, y={dy:.2f}, rot={drot:.0f}")
        else:
            results.append(f"❌ FAIL: {power_name} - Symbol not found in schematic!")
            all_passed = False

    # Print results
    for result in results:
        print(result)

    # Final verdict
    if all_passed:
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED: All power symbols positioned correctly!")
        print("="*70)
        sys.exit(0)
    else:
        print("\n" + "="*70)
        print("❌ SOME TESTS FAILED: Check positions above")
        print("="*70)
        sys.exit(1)
