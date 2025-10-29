#!/usr/bin/env python3
"""
Fixture: PCB with mounting holes.

Creates a PCB with 4 mounting holes in corners (standard M2 holes).
Layout:
- 100mm x 80mm board
- Mounting holes at corners:
  - (3mm, 3mm) - bottom-left
  - (97mm, 3mm) - bottom-right
  - (3mm, 77mm) - top-left
  - (97mm, 77mm) - top-right
- Standard 2.5mm drill diameter for M2 mounting

Used to validate that mounting holes are correctly placed and can be modified.
"""

from circuit_synth import circuit, Component


@circuit(name="mounted_pcb")
def mounted_pcb():
    """Circuit with 4 mounting holes for mechanical assembly."""
    # Add a single resistor for reference
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = mounted_pcb()

    # Define mounting holes
    # Standard positions for 100x80mm board with M2 holes
    mounting_holes = [
        {"position": (3.0, 3.0), "drill_diameter": 2.5, "pad_diameter": 4.0},    # Bottom-left
        {"position": (97.0, 3.0), "drill_diameter": 2.5, "pad_diameter": 4.0},   # Bottom-right
        {"position": (3.0, 77.0), "drill_diameter": 2.5, "pad_diameter": 4.0},   # Top-left
        {"position": (97.0, 77.0), "drill_diameter": 2.5, "pad_diameter": 4.0},  # Top-right
    ]

    circuit_obj.generate_kicad_project(
        project_name="mounted_pcb",
        placement_algorithm="simple",
        generate_pcb=True,
        board_width_mm=100.0,
        board_height_mm=80.0,
        mounting_holes=mounting_holes,
    )

    print("✅ PCB with mounting holes generated successfully!")
    print("📁 Open in KiCad: mounted_pcb/mounted_pcb.kicad_pro")
