#!/usr/bin/env python3
"""
Fixture: Single resistor circuit at 0° rotation.

Used for component orientation tests.
Tests that component rotation can be changed independently from position.
"""

from circuit_synth import circuit, Component


@circuit(name="single_resistor")
def single_resistor():
    """Circuit with a single 10kΩ resistor at default 0° rotation."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = single_resistor()

    circuit_obj.generate_kicad_project(
        project_name="single_resistor",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Single resistor circuit generated successfully!")
    print("📁 Open in KiCad: single_resistor/single_resistor.kicad_pro")
