#!/usr/bin/env python3
"""
Fixture: 4-Layer PCB with Blind Vias.

Creates a 4-layer PCB (F.Cu, In1.Cu, In2.Cu, B.Cu) with 2 blind vias:
- Blind Via 1: F.Cu → In1.Cu (outer to inner, top side)
- Blind Via 2: B.Cu → In2.Cu (outer to inner, bottom side)

Blind vias:
- Connect an outer layer (F.Cu or B.Cu) to an inner layer (In1.Cu or In2.Cu)
- Do NOT touch the opposite outer layer
- Used in HDI (High-Density Interconnect) designs
- Allow component routing to connect to internal planes without drilling through
- Reduce via count and board area needed for routing
"""

from circuit_synth import circuit


@circuit(name="blind_vias_pcb")
def blind_vias_pcb():
    """4-layer PCB with blind vias for HDI interconnect."""
    # This is a blank circuit - PCB is generated with specific via structure
    # Blind vias are added programmatically to the PCB after generation
    pass


if __name__ == "__main__":
    # Generate 4-layer KiCad project when run directly
    circuit_obj = blind_vias_pcb()

    circuit_obj.generate_kicad_project(
        project_name="blind_vias_pcb",
        placement_algorithm="simple",
        generate_pcb=True,
        board_width_mm=100.0,
        board_height_mm=80.0,
    )

    print("✅ Blind vias PCB generated successfully!")
    print("📁 Open in KiCad: blind_vias_pcb/blind_vias_pcb.kicad_pro")
    print("\nNote: Blind vias will be added by the test through direct PCB manipulation")
