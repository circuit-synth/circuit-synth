#!/usr/bin/env python3
"""
Fixture: Two unconnected resistors on same sheet.

Starting point for testing local label creation for readable net naming.
"""

from circuit_synth import *


@circuit(name="two_resistors")
def two_resistors():
    """Circuit with two resistors - NO connection between them."""
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

    # Note: uncomment to add local label connection
    # data_line = Net("DATA_LINE")
    # data_line += r1[1]
    # data_line += r2[1]


if __name__ == "__main__":
    circuit_obj = two_resistors()
    circuit_obj.generate_kicad_project(
        project_name="two_resistors", placement_algorithm="simple", generate_pcb=True
    )
    print("✅ Two unconnected resistors generated!")
    print("📁 Open in KiCad: two_resistors/two_resistors.kicad_pro")
