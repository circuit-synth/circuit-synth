#!/usr/bin/env python3
"""
Fixture: Hierarchical circuit with PowerSupply subcircuit containing resistors.

Demonstrates hierarchical circuit organization for component modification testing:
- Root circuit contains R_main (100k resistor)
- PowerSupply subcircuit contains R1 (1k) and R2 (2k)

Used to test modifying components INSIDE subcircuits (not root sheet).
This addresses the major gap where most tests only operate on root sheet.
"""

from circuit_synth import circuit, Component, Circuit


@circuit(name="subcircuit_with_resistors")
def subcircuit_with_resistors():
    """Hierarchical circuit with PowerSupply subcircuit.

    Root circuit: R_main (100k)
    PowerSupply subcircuit: R1 (1k), R2 (2k)

    Test will modify R1 value in the subcircuit (not root).
    """
    from circuit_synth.core.decorators import get_current_circuit

    root = get_current_circuit()

    # Root circuit component
    r_main = Component(
        symbol="Device:R",
        ref="R_main1",
        value="100k",
        footprint="Resistor_SMD:R_0805_2012Metric",
    )

    # PowerSupply subcircuit
    # START_MARKER: Test will modify R1 value between these markers
    power_supply = Circuit("PowerSupply")

    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="2k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    power_supply.add_component(r1)
    power_supply.add_component(r2)
    # END_MARKER

    root.add_subcircuit(power_supply)


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = subcircuit_with_resistors()

    circuit_obj.generate_kicad_project(
        project_name="subcircuit_with_resistors",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Hierarchical circuit with PowerSupply subcircuit generated!")
    print("📁 Open in KiCad: subcircuit_with_resistors/subcircuit_with_resistors.kicad_pro")
