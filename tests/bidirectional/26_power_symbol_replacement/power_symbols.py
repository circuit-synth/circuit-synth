#!/usr/bin/env python3
"""
Test fixture: Multiple power symbols (VCC, +3V3, +5V, GND, -5V).

Starting point for testing power symbol generation with correct:
- Library references (power:VCC, power:+3V3, etc.)
- Positions relative to component pins
- Rotations (0° for positive supplies, 180° for ground/negative)

Used to test iterative power domain changes and symbol replacement.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="power_symbols")
def power_symbols():
    """Circuit with resistors connected to different power symbols."""

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
    # Generate KiCad project when run directly
    circuit_obj = power_symbols()

    circuit_obj.generate_kicad_project(
        project_name="power_symbols",
        placement_algorithm="simple",
        generate_pcb=True
    )

    print("✅ Power symbols circuit generated!")
    print("📁 Open in KiCad: power_symbols/power_symbols.kicad_pro")
    print("")
    print("Power symbols included:")
    print("  - VCC (positive supply)")
    print("  - +3V3 (3.3V supply)")
    print("  - +5V (5V supply)")
    print("  - GND (ground)")
    print("  - -5V (negative supply)")
