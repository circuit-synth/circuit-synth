#!/usr/bin/env python3
"""
Fixture: Single resistor with power connection capability.

Starting point for testing adding VCC power symbol connection to existing components.
Initially unconnected; VCC net connection is commented out to allow testing.
"""

from circuit_synth import *


@circuit(name="resistor_with_power")
def resistor_with_power():
    """Circuit with single resistor - power connection initially disabled."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Note: uncomment to add power connection
    # vcc = Net(name="VCC")
    # vcc += r1[1]


if __name__ == "__main__":
    circuit_obj = resistor_with_power()
    circuit_obj.generate_kicad_project(
        project_name="resistor_with_power", placement_algorithm="simple", generate_pcb=True
    )
    print("✅ Resistor with power fixture generated!")
    print("📁 Open in KiCad: resistor_with_power/resistor_with_power.kicad_pro")
