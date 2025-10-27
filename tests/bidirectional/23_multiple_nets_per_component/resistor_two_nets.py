#!/usr/bin/env python3
"""
Fixture: Single resistor with pin 1 on NET1 and pin 2 on NET2.

Starting point for testing components participating in multiple nets simultaneously.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="resistor_two_nets")
def resistor_two_nets():
    """Circuit with single resistor participating in two nets."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # R1 pin 1 on NET1
    net1 = Net(name="NET1")
    net1 += r1[1]

    # R1 pin 2 on NET2
    net2 = Net(name="NET2")
    net2 += r1[2]


if __name__ == "__main__":
    circuit_obj = resistor_two_nets()
    circuit_obj.generate_kicad_project(project_name="resistor_two_nets")
    print("✅ Resistor with R1[1] on NET1 and R1[2] on NET2 generated!")
    print("📁 Open in KiCad: resistor_two_nets/resistor_two_nets.kicad_pro")
