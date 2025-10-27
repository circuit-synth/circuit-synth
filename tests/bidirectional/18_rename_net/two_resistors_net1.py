#!/usr/bin/env python3
"""
Fixture: Two resistors connected via NET1.

Starting point for testing renaming a net from NET1 to NET2.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="two_resistors_net1")
def two_resistors_net1():
    """Circuit with two resistors connected via NET1."""
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

    # Connect via NET1
    net1 = Net(name="NET1")
    net1 += r1[1]
    net1 += r2[1]


if __name__ == "__main__":
    circuit_obj = two_resistors_net1()
    circuit_obj.generate_kicad_project(project_name="two_resistors_net1")
    print("✅ Two resistors on NET1 generated!")
    print("📁 Open in KiCad: two_resistors_net1/two_resistors_net1.kicad_pro")
