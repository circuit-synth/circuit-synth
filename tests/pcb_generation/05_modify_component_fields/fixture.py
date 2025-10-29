#!/usr/bin/env python3
"""
Fixture: Single resistor PCB for component field modification test.

Creates a PCB with 1 resistor (R1: 10k, 0603 footprint).
Used to validate that modifying component fields (value, footprint, description, MPN, DNP)
updates correctly without affecting position.
"""

from circuit_synth import circuit, Component


@circuit(name="single_resistor")
def single_resistor():
    """Circuit with single resistor for field modification testing."""
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
