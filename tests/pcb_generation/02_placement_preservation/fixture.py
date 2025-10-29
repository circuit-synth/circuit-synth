#!/usr/bin/env python3
"""
Fixture: Two resistors PCB for placement preservation test.

Creates a simple PCB with 2 resistors (R1, R2).
Used to validate that manual component placement is preserved when circuit changes.
"""

from circuit_synth import circuit, Component


@circuit(name="two_resistors")
def two_resistors():
    """Circuit with two 10kΩ resistors for placement testing."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # ADD R3 HERE


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = two_resistors()

    circuit_obj.generate_kicad_project(
        project_name="two_resistors",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Two resistors circuit generated successfully!")
    print("📁 Open in KiCad: two_resistors/two_resistors.kicad_pro")
