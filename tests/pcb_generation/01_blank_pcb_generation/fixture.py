#!/usr/bin/env python3
"""
Fixture: Blank PCB with board outline.

Creates an empty PCB with a rectangular board outline (200x150mm).
Used for validating basic PCB generation and structure.
"""

from circuit_synth import circuit


@circuit(name="blank_pcb")
def blank_pcb():
    """Circuit with no components - generates blank PCB with board outline."""
    pass


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = blank_pcb()

    circuit_obj.generate_kicad_project(
        project_name="blank_pcb",
        placement_algorithm="simple",
        generate_pcb=True,
        board_width_mm=200.0,
        board_height_mm=150.0,
    )

    print("✅ Blank PCB generated successfully!")
    print("📁 Open in KiCad: blank_pcb/blank_pcb.kicad_pro")
