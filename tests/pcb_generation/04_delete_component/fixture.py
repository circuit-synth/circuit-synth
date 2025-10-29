#!/usr/bin/env python3
"""
Fixture: Three resistors PCB for component deletion test.

Creates a PCB with 3 resistors (R1, R2, R3).
Used to validate that removing a component from Python regenerates correctly,
preserving positions of remaining components.
"""

from circuit_synth import circuit, Component


@circuit(name="three_resistors")
def three_resistors():
    """Circuit with three resistors for component deletion testing."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="22k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="47k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = three_resistors()

    circuit_obj.generate_kicad_project(
        project_name="three_resistors",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Three resistors circuit generated successfully!")
    print("📁 Open in KiCad: three_resistors/three_resistors.kicad_pro")
