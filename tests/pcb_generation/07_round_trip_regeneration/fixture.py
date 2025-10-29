#!/usr/bin/env python3
"""
Fixture: Two resistors PCB for round-trip regeneration test.

Creates a PCB with 2 resistors (R1, R2).
Used to validate complete round-trip workflows with multiple
regeneration cycles, manual changes, and Python modifications.
"""

from circuit_synth import circuit, Component


@circuit(name="round_trip_test")
def round_trip_test():
    """Circuit for round-trip regeneration testing."""
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
    circuit_obj = round_trip_test()

    circuit_obj.generate_kicad_project(
        project_name="round_trip_test",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Round-trip test circuit generated successfully!")
    print("📁 Open in KiCad: round_trip_test/round_trip_test.kicad_pro")
