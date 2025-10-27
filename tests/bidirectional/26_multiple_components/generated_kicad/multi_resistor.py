#!/usr/bin/env python3
"""
Multiple component circuit for testing multi-element handling.

Simple circuit with 2 resistors for testing multiple component scenarios.

Used to test:
- Multiple component generation to KiCad
- Component collection integrity
- Different component types coexistence
- Multi-component round-trip cycles
"""

from circuit_synth import circuit, Component


@circuit(name="multi_component")
def multi_component():
    """Circuit with multiple components."""
    # Create two resistors
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="47k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )


if __name__ == "__main__":
    circuit_obj = multi_component()
    circuit_obj.generate_kicad_project(
        project_name="multi_component",
        placement_algorithm="simple",
        generate_pcb=True,
    )
    print("✅ Multi-component circuit generated successfully!")
