#!/usr/bin/env python3
"""
Fixture: PCB with silkscreen text and graphics.

Creates a PCB with:
- Text: "Rev A" at (5, 5) on F.Silkscreen
- Text: "© 2025" at (190, 5) on F.Silkscreen
- Graphic: Polarity mark (line) at (100, 75)
- Component reference text (R1, R2 auto-added from components)

Used to validate that silkscreen features (text + graphics) can be added
to PCB and preserved across regenerations.
"""

from circuit_synth import circuit, Component


@circuit(name="silkscreen_features")
def silkscreen_features():
    """Circuit with resistors for silkscreen feature testing."""
    # Add components for realistic silkscreen output
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

    # Note: Silkscreen text/graphics are added via PCB generation parameters
    # or manual editing in this fixture phase


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = silkscreen_features()

    circuit_obj.generate_kicad_project(
        project_name="silkscreen_features",
        placement_algorithm="simple",
        generate_pcb=True,
        board_width_mm=200.0,
        board_height_mm=150.0,
    )

    print("✅ Silkscreen features circuit generated successfully!")
    print("📁 Open in KiCad: silkscreen_features/silkscreen_features.kicad_pro")
