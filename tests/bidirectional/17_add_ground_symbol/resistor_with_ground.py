#!/usr/bin/env python3
"""
Fixture: Single resistor, initially unconnected to ground.

Starting point for testing adding ground symbol connections.
Will be modified to add GND connection: r1[2] += Net("GND")
"""

from circuit_synth import *


@circuit(name="resistor_with_ground")
def resistor_with_ground():
    """Circuit with single resistor (initially no ground connection)."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )


if __name__ == "__main__":
    circuit_obj = resistor_with_ground()
    circuit_obj.generate_kicad_project(
        project_name="resistor_with_ground",
        placement_algorithm="simple",
        generate_pcb=True,
    )
    print("✅ Single resistor circuit generated!")
    print("📁 Open in KiCad: resistor_with_ground/resistor_with_ground.kicad_pro")
