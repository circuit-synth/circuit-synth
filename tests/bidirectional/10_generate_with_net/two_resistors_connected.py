#!/usr/bin/env python3
"""
Fixture: Two resistors connected via NET1.

Simplest net test - validates that a named net connection
generates correctly in KiCad schematic.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="two_resistors_connected")
def two_resistors_connected():
    """Circuit with two resistors connected via NET1."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Connect R1 pin 1 to R2 pin 1 via NET1
    net1 = Net(name="NET1")
    net1 += r1[1]
    net1 += r2[1]


if __name__ == "__main__":
    circuit_obj = two_resistors_connected()
    circuit_obj.generate_kicad_project(
        project_name="two_resistors_connected",
        placement_algorithm="simple",
        generate_pcb=True
    )
    print("✅ Two resistors with NET1 connection generated!")
    print("📁 Open in KiCad: two_resistors_connected/two_resistors_connected.kicad_pro")
