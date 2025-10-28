#!/usr/bin/env python3
"""
Fixture: Hierarchical circuit with root and child sheet.

Root sheet contains R1 (10k resistor).
Child sheet contains R2 (4.7k resistor).
Used for testing subcircuit/sheet removal.
"""

from circuit_synth import circuit, Component


@circuit(name="child_sheet")
def child_sheet():
    """Child sheet with a single resistor."""
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )


@circuit(name="hierarchical_circuit")
def hierarchical_circuit():
    """Root circuit with child sheet."""

    # Root sheet component
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Create subcircuit (child sheet)
    # The @circuit decorator automatically adds it as a subcircuit if there's a parent context
    child = child_sheet()


# Generate the circuit
if __name__ == "__main__":
    circuit_obj = hierarchical_circuit()

    # Generate KiCad project (creates hierarchical structure)
    circuit_obj.generate_kicad_project(project_name="hierarchical_circuit")

    # Generate KiCad netlist (required for ratsnest display)
    circuit_obj.generate_kicad_netlist("hierarchical_circuit/hierarchical_circuit.net")

    print("✅ Hierarchical circuit generated successfully!")
    print("📁 Open in KiCad: hierarchical_circuit/hierarchical_circuit.kicad_pro")
