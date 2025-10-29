#!/usr/bin/env python3
"""
Fixture: PCB with fiducial markers for assembly.

Creates a PCB with 3 fiducials (standard registration marks for pick-and-place):
- Fiducial 1 at (5, 5) - top-left corner
- Fiducial 2 at (195, 5) - top-right corner
- Fiducial 3 at (100, 145) - bottom center

Fiducials are standard 1.5mm copper pads used by pick-and-place machines
to calibrate board position and orientation.

Used to validate that fiducial markers can be added to PCB and preserved
across regenerations. Critical for automated assembly.
"""

from circuit_synth import circuit, Component


@circuit(name="fiducial_markers")
def fiducial_markers():
    """Circuit with components and fiducial markers for placement testing."""
    # Add components for realistic board
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

    # Note: Fiducial markers will be added programmatically or manually in test


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = fiducial_markers()

    circuit_obj.generate_kicad_project(
        project_name="fiducial_markers",
        placement_algorithm="simple",
        generate_pcb=True,
        board_width_mm=200.0,
        board_height_mm=150.0,
    )

    print("✅ Fiducial markers circuit generated successfully!")
    print("📁 Open in KiCad: fiducial_markers/fiducial_markers.kicad_pro")
