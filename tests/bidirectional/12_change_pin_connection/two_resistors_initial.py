#!/usr/bin/env python3
"""
Fixture: Two resistors with NET1 connecting R1[1] to R2[1].

Starting point for testing changing pin connections.
"""

from circuit_synth import *


@circuit(name="two_resistors_pin_test")
def two_resistors_pin_test():
    """Circuit with two resistors connected via NET1 on pin 1."""
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

    # Connect R1 pin 1 to R2 pin 1
    net1 = Net("NET1")
    r1[1] += net1
    r2[1] += net1


if __name__ == "__main__":
    circuit_obj = two_resistors_pin_test()
    circuit_obj.generate_kicad_project(
        project_name="two_resistors_pin_test",
        placement_algorithm="simple",
        generate_pcb=True,
    )
    print("✅ Two resistors with NET1 on pin 1 generated!")
    print("📁 Open in KiCad: two_resistors_pin_test/two_resistors_pin_test.kicad_pro")
