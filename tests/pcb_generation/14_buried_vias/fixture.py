#!/usr/bin/env python3
"""
Fixture: 6-Layer PCB with Buried Vias.

Creates a 6-layer PCB (F.Cu, In1.Cu, In2.Cu, In3.Cu, In4.Cu, B.Cu) with 2 buried vias:
- Buried Via 1: In1.Cu → In3.Cu (inner to inner, not touching outer layers)
- Buried Via 2: In2.Cu → In4.Cu (inner to inner, not touching outer layers)

Buried vias:
- Connect ONLY inner layers (never touch F.Cu or B.Cu)
- Used in complex multi-layer boards (6, 8, 10+ layers)
- Allow internal layer interconnection without affecting outer layers
- Enable sophisticated internal routing topologies
- Critical for dense HDI designs with many copper layers
"""

from circuit_synth import circuit


@circuit(name="buried_vias_pcb")
def buried_vias_pcb():
    """6-layer PCB with buried vias for internal layer interconnect."""
    # This is a blank circuit - PCB is generated with specific via structure
    # Buried vias are added programmatically to the PCB after generation
    pass


if __name__ == "__main__":
    # Generate 6-layer KiCad project when run directly
    circuit_obj = buried_vias_pcb()

    circuit_obj.generate_kicad_project(
        project_name="buried_vias_pcb",
        placement_algorithm="simple",
        generate_pcb=True,
        board_width_mm=100.0,
        board_height_mm=80.0,
    )

    print("✅ Buried vias PCB generated successfully!")
    print("📁 Open in KiCad: buried_vias_pcb/buried_vias_pcb.kicad_pro")
    print("\nNote: Buried vias will be added by the test through direct PCB manipulation")
