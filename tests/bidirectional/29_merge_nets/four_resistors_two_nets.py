#!/usr/bin/env python3
"""
Fixture: Four resistors on two separate nets (R1-R2 on NET1, R3-R4 on NET2).

Starting point for testing merging two nets into one net.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="four_resistors_two_nets")
def four_resistors_two_nets():
    """Circuit with four resistors on two separate nets."""
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
    r4 = Component(
        symbol="Device:R",
        ref="R4",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # R1-R2 on NET1
    net1 = Net(name="NET1")
    net1 += r1[1]
    net1 += r2[1]

    # R3-R4 on NET2
    net2 = Net(name="NET2")
    net2 += r3[1]
    net2 += r4[1]


if __name__ == "__main__":
    circuit_obj = four_resistors_two_nets()
    circuit_obj.generate_kicad_project(project_name="four_resistors_two_nets")
    print("✅ Four resistors on two nets (NET1: R1-R2, NET2: R3-R4) generated!")
    print("📁 Open in KiCad: four_resistors_two_nets/four_resistors_two_nets.kicad_pro")
