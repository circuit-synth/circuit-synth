#!/usr/bin/env python3
"""
Fixture: Hierarchical circuit with root sheet and child sheet.

Demonstrates hierarchical circuit organization:
- Root sheet contains R1 (resistor)
- Child sheet (subcircuit) contains R2 (resistor)

Used to test adding subcircuits (child sheets) during iterative development.
"""

from circuit_synth import circuit, Component, Circuit


@circuit(name="ChildSheet")
def child_sheet():
    """Child circuit with R2 on child sheet."""
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )


@circuit(name="hierarchical_circuit")
def hierarchical_circuit():
    """Root circuit with R1 on root sheet.

    Note: This uses the root-only version by default.
    The test will modify this to add the subcircuit section.
    """
    from circuit_synth.core.decorators import get_current_circuit

    root = get_current_circuit()

    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    # START_MARKER: Test will modify between these markers
    # Call the child sheet circuit to add it as a subcircuit
    child_sheet()
    # END_MARKER


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = hierarchical_circuit()

    circuit_obj.generate_kicad_project(
        project_name="hierarchical_circuit",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Hierarchical circuit generated successfully!")
    print("📁 Open in KiCad: hierarchical_circuit/hierarchical_circuit.kicad_pro")
