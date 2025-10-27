#!/usr/bin/env python3
"""
Fixture: Single resistor circuit.

Simplest non-empty circuit: one 10kΩ resistor.
Used for basic generation and import tests.
"""

from circuit_synth import circuit, Component


@circuit(name="single_resistor")
def single_resistor():
    """Circuit with a single 10kΩ resistor."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
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
