#!/usr/bin/env python3
"""
Fixture: Single isolated resistor with NO net connections.

Starting point for testing isolated component handling.
This is the initial state - R1 exists but has no electrical connections.
"""

from circuit_synth import *


@circuit(name="isolated_resistor")
def isolated_resistor():
    """Circuit with a single resistor - NO connections to any pins."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Note: uncomment to connect pin 1
    # net1 = Net("NET1")
    # r1[1] += net1


if __name__ == "__main__":
    circuit_obj = isolated_resistor()
    circuit_obj.generate_kicad_project(
        project_name="isolated_resistor", placement_algorithm="simple", generate_pcb=True
    )
    print("✅ Isolated resistor generated!")
    print("📁 Open in KiCad: isolated_resistor/isolated_resistor.kicad_pro")

