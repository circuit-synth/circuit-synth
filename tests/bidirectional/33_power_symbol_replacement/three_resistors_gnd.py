#!/usr/bin/env python3
"""
Fixture: Three resistors connected to GND via hierarchical labels.

Starting point for testing what happens when user manually replaces
hierarchical labels with KiCad power symbols.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="three_resistors_gnd")
def three_resistors_gnd():
    """Circuit with three resistors all connected to GND."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="2.2k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Connect all to GND (generates hierarchical labels)
    gnd = Net(name="GND")
    gnd += r1[2]
    gnd += r2[2]
    gnd += r3[2]


if __name__ == "__main__":
    circuit_obj = three_resistors_gnd()
    circuit_obj.generate_kicad_project(project_name="three_resistors_gnd")
    print("✅ Three resistors with GND hierarchical labels generated!")
    print("📁 Open in KiCad: three_resistors_gnd/three_resistors_gnd.kicad_pro")
    print("")
    print("⚠️  NEXT STEP: Manually replace GND hierarchical labels with power symbols")
