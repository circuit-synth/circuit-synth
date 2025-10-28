#!/usr/bin/env python3
"""
Fixture: Circuit testing reference collision detection.

Tests both:
1. Duplicate references on same sheet (should fail or auto-rename)
2. Same reference on different hierarchical sheets (should work with hierarchical paths)

Used for testing reference uniqueness validation and hierarchical path disambiguation.
"""

from circuit_synth import circuit, Component, Net, Circuit


@circuit(name="duplicate_refs")
def duplicate_refs():
    """Circuit testing reference collision detection.

    Tests two scenarios:
    1. Same sheet collision: Try to create two R1 on root sheet
    2. Global uniqueness: R1 on root and R2 on child sheet

    Expected behaviors:
    - Same sheet: Error raised (reference collision)
    - Different sheets: R2 used (circuit-synth enforces global uniqueness)

    Note: circuit-synth enforces GLOBAL reference uniqueness across entire
    hierarchy, which is stricter than KiCad's per-sheet uniqueness.
    """
    # Create root circuit components
    r1_root = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0805_2012Metric",
    )

    # Try to create another R1 on the same sheet
    # This should either fail or auto-rename to R2
    # START_MARKER_SAME_SHEET
    # END_MARKER_SAME_SHEET

    # Create hierarchical subcircuit with R2
    # Note: circuit-synth enforces global reference uniqueness across entire hierarchy
    # Unlike KiCad which allows same reference on different sheets with hierarchical paths
    child_sheet = Circuit("SubCircuit")

    r2_child = Component(
        symbol="Device:R",
        ref="R2",  # Different reference - circuit-synth requires global uniqueness
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    child_sheet.add_component(r2_child)

    # Add child sheet to root
    # Note: We need to access the root circuit to add subcircuit
    # This will be done in the return statement's circuit object


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = duplicate_refs()

    # Add subcircuit to root
    child_sheet = Circuit("SubCircuit")
    r2_child = Component(
        symbol="Device:R",
        ref="R2",  # Different reference - circuit-synth requires global uniqueness
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    child_sheet.add_component(r2_child)

    # Add subcircuit
    circuit_obj.add_subcircuit(child_sheet)

    circuit_obj.generate_kicad_project(
        project_name="duplicate_refs",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Circuit with reference collision test generated successfully!")
    print("📁 Open in KiCad: duplicate_refs/duplicate_refs.kicad_pro")
    print("📋 Test scenarios:")
    print("   1. Same sheet collision: (test will inject second R1 on root)")
    print("   2. Global uniqueness: R1 on root, R2 on SubCircuit")
    print("🔍 Verify:")
    print("   - Root sheet has R1 (10k)")
    print("   - SubCircuit sheet has R2 (4.7k)")
    print("   - circuit-synth enforces global reference uniqueness")
