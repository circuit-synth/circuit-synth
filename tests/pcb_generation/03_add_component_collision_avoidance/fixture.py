#!/usr/bin/env python3
"""
Fixture: Two resistors PCB for component addition test.

Creates a PCB with initial 2 resistors (R1, R2).
Used to test adding components with smart auto-placement and collision avoidance.
"""

from circuit_synth import circuit, Component


@circuit(name="add_component_test")
def add_component_test():
    """Circuit for testing component addition with collision avoidance."""
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

    # ADD R3 HERE


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = add_component_test()

    circuit_obj.generate_kicad_project(
        project_name="add_component_test",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Add component test circuit generated successfully!")
    print("📁 Open in KiCad: add_component_test/add_component_test.kicad_pro")
