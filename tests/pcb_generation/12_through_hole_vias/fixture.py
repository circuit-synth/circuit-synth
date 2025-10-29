#!/usr/bin/env python3
"""
Fixture: 4-Layer PCB with Through-Hole Vias.

Creates a 4-layer PCB (F.Cu, In1.Cu, In2.Cu, B.Cu) with 3 through-hole vias that
connect all 4 layers. Through-hole vias are used for power distribution and signal
routing across multiple internal layers.

Through-hole vias:
- Connect ALL layers (F.Cu → B.Cu via internal layers)
- Typically 0.3-0.5mm drill diameter
- Used for power/ground distribution in multi-layer boards
- Via 1 at (10mm, 10mm)
- Via 2 at (20mm, 20mm)
- Via 3 at (30mm, 30mm)
"""

from circuit_synth import circuit


@circuit(name="through_hole_vias_pcb")
def through_hole_vias_pcb():
    """4-layer PCB with through-hole vias for power distribution."""
    # This is a blank circuit - PCB is generated with specific via structure
    # Vias are added programmatically to the PCB after generation
    pass


if __name__ == "__main__":
    # Generate 4-layer KiCad project when run directly
    circuit_obj = through_hole_vias_pcb()

    circuit_obj.generate_kicad_project(
        project_name="through_hole_vias_pcb",
        placement_algorithm="simple",
        generate_pcb=True,
        board_width_mm=100.0,
        board_height_mm=80.0,
    )

    print("✅ Through-hole vias PCB generated successfully!")
    print("📁 Open in KiCad: through_hole_vias_pcb/through_hole_vias_pcb.kicad_pro")
    print("\nNote: Vias will be added by the test through direct PCB manipulation")
