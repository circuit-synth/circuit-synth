#!/usr/bin/env python3
"""
Fixture: Four resistors on two separate nets.

Starting point for testing net merging functionality.
- NET1: R1 and R2
- NET2: R3 and R4

When merging, all four will connect to NET1 and NET2 will be deleted.
"""

from circuit_synth import *


@circuit(name="four_resistors")
def four_resistors():
    """Circuit with four resistors on two separate nets."""
    # NET1: R1 and R2
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

    # NET2: R3 and R4
    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="22k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r4 = Component(
        symbol="Device:R",
        ref="R4",
        value="47k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Create two separate nets
    net1 = Net(name="NET1")
    net1 += r1[1]
    net1 += r2[1]

    net2 = Net(name="NET2")
    net2 += r3[1]
    net2 += r4[1]


if __name__ == "__main__":
    circuit_obj = four_resistors()
    circuit_obj.generate_kicad_project(
        project_name="four_resistors", placement_algorithm="simple", generate_pcb=True
    )
    print("✅ Four resistors on two separate nets generated!")
    print("📁 Open in KiCad: four_resistors/four_resistors.kicad_pro")
    print("📊 View nets:")
    print("   - NET1: R1[1], R2[1]")
    print("   - NET2: R3[1], R4[1]")
