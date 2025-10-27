#!/usr/bin/env python3
"""
Fixture: Three resistors connected via NET1.

Starting point for testing removing a component from an existing net.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="three_resistors_on_net")
def three_resistors_on_net():
    """Circuit with three resistors connected via NET1."""
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

    # Connect all three resistors via NET1
    net1 = Net(name="NET1")
    net1 += r1[1]
    net1 += r2[1]
    net1 += r3[1]


if __name__ == "__main__":
    circuit_obj = three_resistors_on_net()
    circuit_obj.generate_kicad_project(project_name="three_resistors_on_net")
    print("✅ Three resistors on NET1 generated!")
    print("📁 Open in KiCad: three_resistors_on_net/three_resistors_on_net.kicad_pro")
