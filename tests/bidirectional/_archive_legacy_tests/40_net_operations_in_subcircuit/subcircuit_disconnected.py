#!/usr/bin/env python3
"""
Fixture: Hierarchical circuit with subcircuit containing disconnected resistors.

Demonstrates hierarchical circuit with isolated components on child sheet:
- Root sheet: Empty (just contains subcircuit reference)
- Subcircuit sheet: R1 (10k) and R2 (4.7k) - NO connection between them

Used to test net operations within hierarchical sheets (not root sheet).
"""

from circuit_synth import circuit, Component, Circuit, Net


@circuit(name="subcircuit_disconnected")
def subcircuit_disconnected():
    """Root circuit with subcircuit containing disconnected resistors.

    The root sheet is empty except for the subcircuit reference.
    The subcircuit "SubCircuit" contains R1 and R2 with NO connection.
    The test will modify this to add a net connecting them.
    """
    from circuit_synth.core.decorators import get_current_circuit

    root = get_current_circuit()

    # Create subcircuit with two disconnected resistors
    sub = Circuit("SubCircuit")

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

    sub.add_component(r1)
    sub.add_component(r2)

    # START_MARKER: Test will add net connection between these markers
    # Test will inject:
    #   net1 = Net("NET1")
    #   r1[1] += net1
    #   r2[2] += net1
    # END_MARKER

    root.add_subcircuit(sub)


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = subcircuit_disconnected()

    circuit_obj.generate_kicad_project(
        project_name="subcircuit_disconnected",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Hierarchical circuit with disconnected resistors generated!")
    print("📁 Open in KiCad: subcircuit_disconnected/subcircuit_disconnected.kicad_pro")
    print("\n📋 Structure:")
    print("   - Root sheet: Empty (contains subcircuit reference)")
    print("   - SubCircuit sheet: R1 (10k), R2 (4.7k) - NOT connected")
