#!/usr/bin/env python3
"""
Fixture: Hierarchical circuit with empty subcircuit.

Demonstrates hierarchical circuit organization with empty child sheet:
- Root sheet contains R1 (resistor)
- Child sheet (subcircuit) initially empty (no components)

Used to test empty sheet handling and dynamic component addition.
"""

from circuit_synth import circuit, Component


@circuit
def placeholder_subcircuit():
    """Empty subcircuit - placeholder for future components.

    Initially empty. Test will add components by uncommenting code below.
    """
    # START_MARKER: Test will modify between these markers to add/remove components
    # Uncomment to add components to subcircuit:
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    # END_MARKER
    pass


@circuit(name="empty_subcircuit")
def main():
    """Root circuit with R1 and empty placeholder subcircuit.

    The root sheet has R1. The placeholder_subcircuit is called but contains
    no components initially. The test validates empty sheet handling and will
    modify the subcircuit to add components dynamically.
    """
    # Component on root sheet
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Call empty subcircuit - creates hierarchical sheet with no components
    placeholder_subcircuit()


if __name__ == "__main__":
    circuit_obj = main()
    circuit_obj.generate_kicad_project(project_name="empty_subcircuit")

    print("✅ Empty subcircuit circuit generated successfully!")
    print("📁 Open in KiCad: empty_subcircuit/empty_subcircuit.kicad_pro")
    print("📋 Root sheet: R1 (resistor)")
    print("📄 Child sheet: placeholder_subcircuit_1 (initially empty)")
