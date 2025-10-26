#!/usr/bin/env python3
"""
Fixture: Two resistors circuit (no connections).

Two resistors without connections.
Used for testing net creation and deletion.
"""

from circuit_synth import circuit, Component


@circuit(name="two_resistors")
def two_resistors():
    """Circuit with two resistors, no connections."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="20k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )


if __name__ == "__main__":
    circuit_obj = two_resistors()
    circuit_obj.generate_kicad_project(
        project_name="two_resistors",
        placement_algorithm="simple",
        generate_pcb=True,
    )
    print("✅ Two resistors circuit generated successfully!")
    print("📁 Open in KiCad: two_resistors/two_resistors.kicad_pro")
