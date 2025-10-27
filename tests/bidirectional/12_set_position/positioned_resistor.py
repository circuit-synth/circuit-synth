#!/usr/bin/env python3
"""
Fixture: Positioned resistor circuit.

Two resistors with explicit positions.
Used for testing position preservation.
"""

from circuit_synth import circuit, Component


@circuit(name="positioned_resistor")
def positioned_resistor():
    """Circuit with two positioned resistors."""
    # First resistor at specific position
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
        at=(100.0, 100.0, 0),  # X=100mm, Y=100mm, rotation=0°
    )

    # Second resistor at different position
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="20k",
        footprint="Resistor_SMD:R_0603_1608Metric",
        at=(150.0, 100.0, 90),  # X=150mm, Y=100mm, rotation=90°
    )


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = positioned_resistor()

    circuit_obj.generate_kicad_project(
        project_name="positioned_resistor",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Positioned resistor circuit generated successfully!")
    print("📁 Open in KiCad: positioned_resistor/positioned_resistor.kicad_pro")
