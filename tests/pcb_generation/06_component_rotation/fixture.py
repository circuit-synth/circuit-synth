#!/usr/bin/env python3
"""
Fixture: Two resistors PCB for component rotation test.

Creates a PCB with 2 resistors (R1, R2).
Used to validate that modifying component rotation angle works correctly.
"""

from circuit_synth import circuit, Component


@circuit(name="rotation_test")
def rotation_test():
    """Circuit with two resistors for rotation testing."""
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


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = rotation_test()

    circuit_obj.generate_kicad_project(
        project_name="rotation_test",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Rotation test circuit generated successfully!")
    print("📁 Open in KiCad: rotation_test/rotation_test.kicad_pro")
