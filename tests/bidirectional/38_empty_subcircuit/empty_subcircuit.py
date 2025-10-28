#!/usr/bin/env python3
"""
Fixture: Hierarchical circuit with empty subcircuit.

Demonstrates hierarchical circuit organization with empty child sheet:
- Root sheet contains R1 (resistor)
- Child sheet (subcircuit) initially empty (no components)

Used to test empty sheet handling and dynamic component addition.
"""

from circuit_synth import circuit, Component, Circuit


@circuit(name="empty_subcircuit")
def empty_subcircuit():
    """Root circuit with R1 on root sheet and empty subcircuit.

    The root sheet has R1. A child circuit is created but left empty initially.
    The test will modify this to add/remove components from the subcircuit.
    """
    from circuit_synth.core.decorators import get_current_circuit

    root = get_current_circuit()

    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Create empty subcircuit (no components)
    empty_sub = Circuit("EmptySubcircuit")
    # START_MARKER: Test will modify between these markers to add/remove components
    # END_MARKER
    root.add_subcircuit(empty_sub)


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = empty_subcircuit()

    circuit_obj.generate_kicad_project(
        project_name="empty_subcircuit",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Empty subcircuit circuit generated successfully!")
    print("📁 Open in KiCad: empty_subcircuit/empty_subcircuit.kicad_pro")
