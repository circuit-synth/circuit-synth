#!/usr/bin/env python3
"""
Single resistor circuit for testing bidirectional sync.

This is the simplest non-empty circuit: one 10kΩ resistor.

Used to test:
- Basic component creation and footprint selection
- Python → KiCad generation with components
- KiCad → Python import with component extraction
- Component property preservation (reference, value, footprint)
"""

from circuit_synth import circuit, Component


@circuit(name="single_resistor")
def single_resistor():
    """Circuit with a single 10kΩ resistor."""
    # Create a single resistor with value 10k
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
