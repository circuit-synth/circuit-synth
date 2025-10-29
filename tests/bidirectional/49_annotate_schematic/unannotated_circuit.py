#!/usr/bin/env python3
"""
Fixture: Unannotated circuit with components R?, R?, C?.

Represents the common workflow where components are defined
without specific reference designator numbers during initial design,
expecting KiCad's annotation tool to assign sequential numbers.

This tests the critical bidirectional sync capability for handling
reference designator annotation/renaming while preserving component
identity through UUID matching (Issue #369).
"""

from circuit_synth import circuit, Component, Net


@circuit(name="unannotated_circuit")
def unannotated_circuit():
    """Circuit with unannotated components (R?, C?).

    Tests that:
    1. Unannotated references (R?, R?, C?) generate successfully
    2. After KiCad annotation (R1, R2, C1), sync recognizes same components via UUID
    3. Reference updates from ? to numbered work correctly
    4. Positions are preserved through annotation
    5. Nets update to use new references
    """

    # Create components with unannotated references
    # This is common practice: use ? placeholder for initial design,
    # then let KiCad's annotation tool assign sequential numbers
    r1 = Component(
        symbol="Device:R",
        ref="R?",  # Unannotated - KiCad will assign R1, R2, etc.
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r2 = Component(
        symbol="Device:R",
        ref="R?",  # Another unannotated resistor
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    c1 = Component(
        symbol="Device:C",
        ref="C?",  # Unannotated capacitor
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )

    # Create a simple net to test net reference updates
    # After annotation, this net should show R1, R2, C1 instead of R?, R?, C?
    net1 = Net(name="signal")
    r1[1] += net1
    c1[1] += net1

    net2 = Net(name="output")
    r2[1] += net2
    c1[2] += net2


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = unannotated_circuit()

    circuit_obj.generate_kicad_project(project_name="unannotated_circuit")

    print("✅ Unannotated circuit generated successfully!")
    print("📁 Open in KiCad: unannotated_circuit/unannotated_circuit.kicad_pro")
    print("💡 Notice: Components have ? references (R?, R?, C?)")
    print("🔧 Next: Use KiCad's annotation tool to assign R1, R2, C1")
    print("   Tools > Annotate Schematic > Annotate")
