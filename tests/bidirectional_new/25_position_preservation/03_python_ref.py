#!/usr/bin/env python3
"""
Positioned resistor circuit for testing position preservation.

This circuit has a single 10kΩ resistor with explicit position information.

Used to test:
- Component position extraction from KiCad
- Position preservation through Python → KiCad → Python cycle
- Manual position changes surviving round-trip
- Position stability on repeated cycles
- Rotation angle preservation with position
"""

from circuit_synth import circuit, Component


@circuit(name="positioned_resistor")
def positioned_resistor():
    """Circuit with a single 10kΩ resistor with position information."""
    # Create a single resistor with value 10k
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    # Note: Position (X, Y) and rotation will be extracted from KiCad
    # and preserved through round-trip cycles


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
