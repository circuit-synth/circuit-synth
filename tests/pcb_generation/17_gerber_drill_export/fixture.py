#!/usr/bin/env python3
"""
Fixture: Simple 2-layer PCB for Gerber and drill file export testing.

Creates a simple PCB with:
- 2 resistors (R1, R2)
- 1 capacitor (C1)
- 4 mounting holes
- Board outline

Used to validate that Gerber and drill files (manufacturing output) are
generated correctly and can be submitted to PCB manufacturers.
"""

from circuit_synth import circuit, Component


@circuit(name="gerber_drill_export")
def gerber_drill_export():
    """Simple circuit for Gerber/drill export validation."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="22k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )

    # Note: Mounting holes are typically added to PCB after generation


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = gerber_drill_export()

    circuit_obj.generate_kicad_project(
        project_name="gerber_drill_export",
        placement_algorithm="simple",
        generate_pcb=True,
        board_width_mm=200.0,
        board_height_mm=150.0,
    )

    print("✅ Gerber/drill export test circuit generated successfully!")
    print("📁 Open in KiCad: gerber_drill_export/gerber_drill_export.kicad_pro")
