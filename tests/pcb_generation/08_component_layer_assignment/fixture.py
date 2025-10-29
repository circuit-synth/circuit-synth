#!/usr/bin/env python3
"""
Fixture: Double-sided PCB with components on different layers.

Creates a PCB with 2 resistors:
- R1 on F.Cu (front/top layer)
- R2 on B.Cu (back/bottom layer)

Used to validate that component layer assignments work correctly and
can be modified in Python, then regenerated.
"""

from circuit_synth import circuit, Component


@circuit(name="double_sided_pcb")
def double_sided_pcb():
    """Circuit with two resistors on different layers for layer assignment testing."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r1.layer = "F.Cu"  # Front/top layer

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r2.layer = "B.Cu"  # Back/bottom layer


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = double_sided_pcb()

    circuit_obj.generate_kicad_project(
        project_name="double_sided_pcb",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Double-sided PCB generated successfully!")
    print("📁 Open in KiCad: double_sided_pcb/double_sided_pcb.kicad_pro")
