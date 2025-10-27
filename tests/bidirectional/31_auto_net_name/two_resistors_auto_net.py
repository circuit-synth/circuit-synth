#!/usr/bin/env python3
"""
Fixture: Two resistors connected via auto-generated net name (name=None).

Starting point for testing behavior when net name is not specified.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="two_resistors_auto_net")
def two_resistors_auto_net():
    """Circuit with two resistors connected via auto-generated net name."""
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

    # Connect via net with auto-generated name
    net1 = Net(name=None)  # or just Net() with no name parameter
    net1 += r1[1]
    net1 += r2[1]


if __name__ == "__main__":
    circuit_obj = two_resistors_auto_net()
    circuit_obj.generate_kicad_project(project_name="two_resistors_auto_net")
    print("✅ Two resistors with auto-generated net name generated!")
    print("📁 Open in KiCad: two_resistors_auto_net/two_resistors_auto_net.kicad_pro")
    print("🔍 Check schematic to see what net name was auto-generated")
