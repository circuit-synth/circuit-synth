#!/usr/bin/env python3
"""
Fixture: Two resistors connected R1[1]-R2[1] via NET1.

Starting point for testing changing which pins are connected on the same net.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="two_resistors_pin_change")
def two_resistors_pin_change():
    """Circuit with two resistors connected via NET1 on pins 1."""
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

    # Connect R1[1] to R2[1] via NET1
    net1 = Net(name="NET1")
    net1 += r1[1]
    net1 += r2[1]


if __name__ == "__main__":
    circuit_obj = two_resistors_pin_change()
    circuit_obj.generate_kicad_project(project_name="two_resistors_pin_change")
    print("✅ Two resistors connected R1[1]-R2[1] on NET1 generated!")
    print("📁 Open in KiCad: two_resistors_pin_change/two_resistors_pin_change.kicad_pro")
