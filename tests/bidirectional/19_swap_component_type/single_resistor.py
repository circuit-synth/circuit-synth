#!/usr/bin/env python3
"""
Fixture: Single resistor circuit for component type swap test.

This circuit starts with a single 10kΩ resistor (Device:R).
The test will change this to a capacitor (Device:C) while keeping
the reference as "R1" and position preserved.

Used for testing component symbol type changes during iterative design.
"""

from circuit_synth import circuit, Component


@circuit(name="single_resistor")
def single_resistor():
    """Circuit with a single resistor (Device:R).

    Will be swapped to capacitor (Device:C) during test while keeping:
    - Reference: R1 (unchanged)
    - Position: preserved via UUID matching
    """

    # Create single resistor component
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = single_resistor()

    circuit_obj.generate_kicad_project(project_name="single_resistor")

    print("✅ Single resistor circuit generated successfully!")
    print("📁 Open in KiCad: single_resistor/single_resistor.kicad_pro")
