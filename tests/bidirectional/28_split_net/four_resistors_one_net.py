#!/usr/bin/env python3
"""
Fixture: Four resistors all connected via NET1.

Starting point for testing splitting one net into two separate nets.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="four_resistors_one_net")
def four_resistors_one_net():
    """Circuit with four resistors all connected via NET1."""
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

    # Connect all four resistors via NET1
    net1 = Net(name="NET1")
    net1 += r1[1]
    net1 += r2[1]
    net1 += r3[1]
    net1 += r4[1]


if __name__ == "__main__":
    circuit_obj = four_resistors_one_net()
    circuit_obj.generate_kicad_project(project_name="four_resistors_one_net")
    print("✅ Four resistors all on NET1 generated!")
    print("📁 Open in KiCad: four_resistors_one_net/four_resistors_one_net.kicad_pro")
