#!/usr/bin/env python3
"""
Fixture: Base circuit for incremental growth test.

Starting point: Two resistors (R1, R2).
This circuit will be incrementally expanded through multiple round-trips.
"""

from circuit_synth import circuit, Component


@circuit(name="growing_circuit")
def growing_circuit():
    """Base circuit with two resistors for incremental growth testing."""

    # Initial components - Day 1
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = growing_circuit()

    circuit_obj.generate_kicad_project(project_name="growing_circuit")

    print("✅ Base circuit generated successfully!")
    print("📁 Open in KiCad: growing_circuit/growing_circuit.kicad_pro")
    print("\nNext steps:")
    print("1. Run: uv run kicad-to-python growing_circuit stage1.py")
    print("2. Edit stage1.py to add a capacitor")
    print("3. Run: uv run stage1.py")
