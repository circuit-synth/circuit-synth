#!/usr/bin/env python3
"""Base circuit for test 51: sync_after_external_edit

Creates a simple circuit with two resistors.
This circuit will be:
1. Generated from Python
2. Modified externally (simulated)
3. Synchronized back to Python
4. Modified again in Python
"""

from circuit_synth import circuit, Component


@circuit(name="base_circuit")
def base_circuit():
    """Circuit with two resistors for testing external edit synchronization.

    R1 will have its value changed externally (1k -> 1.5k)
    R2 will have its position changed externally
    R3 will be added externally (3.3k)
    R4 will be added in Python (4.7k)
    """

    # Create two resistors
    # External edits will:
    # - Change R1 value to 1.5k
    # - Move R2 to (160, 110)
    # - Add R3 (3.3k)
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
        at=(100, 100, 0),
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="2k",
        footprint="Resistor_SMD:R_0603_1608Metric",
        at=(150, 100, 0),
    )


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = base_circuit()

    circuit_obj.generate_kicad_project(project_name="base_circuit")

    print("✅ Base circuit generated successfully!")
    print("📁 Open in KiCad: base_circuit/base_circuit.kicad_pro")
