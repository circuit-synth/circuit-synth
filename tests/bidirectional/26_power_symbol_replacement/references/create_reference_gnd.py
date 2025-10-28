#!/usr/bin/env python3
"""
Create reference project for GND power symbol.
This will be manually corrected in KiCad to create the reference.
"""

from circuit_synth import circuit, Component, Net

@circuit(name="reference_gnd")
def reference_gnd():
    """Reference circuit: Single resistor connected to GND."""
    # Create resistor
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
    circuit_obj = reference_gnd()
    circuit_obj.generate_kicad_project(project_name="reference_gnd")

    print("✅ Reference GND project generated!")
    print("📁 Location: reference_gnd/reference_gnd.kicad_pro")
    print("")
    print("📋 MANUAL STEPS:")
    print("1. Open reference_gnd/reference_gnd.kicad_pro in KiCad")
    print("2. The resistor R1 should be placed on the schematic")
    print("3. Add a GND power symbol at R1 pin 2 (bottom pin)")
    print("4. Position the GND symbol correctly (touching the pin)")
    print("5. Save the schematic")
    print("")
    print("Expected layout:")
    print("  - R1 resistor (vertical orientation)")
    print("  - Pin 1 (top): orientation 270°")
    print("  - Pin 2 (bottom): orientation 90°, connected to GND")
    print("  - GND symbol: placed at pin 2, pointing downward")
