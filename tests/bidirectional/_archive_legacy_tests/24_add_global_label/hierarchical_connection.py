#!/usr/bin/env python3
"""
Test fixture: Cross-sheet hierarchical label connection.

Demonstrates passing a net between parent and child circuits to establish
cross-sheet electrical connectivity via hierarchical labels and pins.

Used to test the critical iterative workflow:
1. Start with 2 circuits (parent + child), components unconnected
2. Pass net from parent to child to connect components across sheets
3. Verify hierarchical sheet symbol, pins, and labels are generated
"""

from circuit_synth import circuit, Component, Net


@circuit(name="child_circuit")
def child_circuit():
    """Child circuit with one resistor - initially unconnected."""
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    # START_MARKER: Test will add net connection between markers
    # END_MARKER


@circuit(name="parent_circuit")
def parent_circuit():
    """Parent circuit with one resistor - initially unconnected."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # START_MARKER: Test will add net passing between markers
    child_circuit()
    # END_MARKER


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = parent_circuit()

    circuit_obj.generate_kicad_project(
        project_name="hierarchical_connection",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Hierarchical circuit generated successfully!")
    print("📁 Open in KiCad: hierarchical_connection/hierarchical_connection.kicad_pro")
