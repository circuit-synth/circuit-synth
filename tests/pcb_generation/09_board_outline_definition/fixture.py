#!/usr/bin/env python3
"""
Fixture: PCB with custom board outline.

Creates a PCB with a non-rectangular board outline:
- L-shaped outline (like an L shape)
- Demonstrates custom form factor design

This tests that circuit-synth can define and generate
non-standard board shapes, important for:
- Enclosure-constrained designs
- Modular designs
- Complex mechanical assemblies
"""

from circuit_synth import circuit, Component


@circuit(name="custom_outline_pcb")
def custom_outline_pcb():
    """Circuit with custom L-shaped board outline."""
    # Add a single resistor for reference
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = custom_outline_pcb()

    # Define custom board outline (L-shaped)
    # Points define the outline boundary in mm
    # For an L-shape:
    # - Horizontal rectangle on top: 100mm wide x 40mm tall
    # - Vertical extension below: 40mm wide x 50mm tall
    # - Creates L-shaped PCB
    board_outline_points = [
        (0, 0),        # Bottom-left (0,0)
        (100, 0),      # Bottom-right (100,0)
        (100, 40),     # Top-right of horizontal section
        (40, 40),      # Notch point (step inward)
        (40, 90),      # Bottom-right of vertical section
        (0, 90),       # Top-left of vertical section
    ]

    circuit_obj.generate_kicad_project(
        project_name="custom_outline_pcb",
        placement_algorithm="simple",
        generate_pcb=True,
        board_outline=board_outline_points,
    )

    print("✅ Custom outline PCB generated successfully!")
    print("📁 Open in KiCad: custom_outline_pcb/custom_outline_pcb.kicad_pro")
