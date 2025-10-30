#!/usr/bin/env python3
"""
Fixture: Hierarchical voltage divider subcircuit test.

Tests creating multiple hierarchical subcircuits (subsheets) with the same circuit pattern.

Initial: One voltage divider subcircuit (divider_1)
Modified: Two voltage divider subcircuits (divider_1 + divider_2) - uncomment second instance

Real-world use case: Reusable circuit blocks in separate sheets like sensor inputs, LED drivers, etc.
This demonstrates circuit-synth's hierarchical design capability.
"""

from circuit_synth import circuit, Component, Net


@circuit
def voltage_divider_subcircuit(vcc_net: Net, gnd_net: Net):
    """Create a voltage divider subcircuit on its own sheet.

    This will appear as a hierarchical sheet symbol in the parent circuit.

    Args:
        vcc_net: Power supply net to connect to parent (hierarchical pin)
        gnd_net: Ground net to connect to parent (hierarchical pin)

    Returns:
        Net: The output net (voltage divider output as hierarchical pin)
    """
    # Create two resistors for this divider
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Connect R1 top to VCC (hierarchical input)
    vcc_net += r1[1]

    # Create output net (junction between R1 and R2)
    output_net = Net(name="VOUT")
    output_net += r1[2]
    output_net += r2[1]

    # Connect R2 bottom to GND (hierarchical input)
    gnd_net += r2[2]

    return output_net  # This becomes a hierarchical output pin


@circuit(name="voltage_divider_instances")
def voltage_divider_instances():
    """Circuit demonstrating multiple hierarchical subcircuit instances.

    Initial: One voltage divider subcircuit (divider_1)
    Modified: Two voltage divider subcircuits (divider_1 + divider_2)

    Each subcircuit appears as a sheet symbol in the parent, with its own subsheet.
    Both subcircuits share common VCC and GND nets from parent.
    """
    # Shared power nets in parent circuit
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # Create first voltage divider subcircuit (always present)
    # Auto-named as "voltage_divider_subcircuit_1"
    vout_1 = voltage_divider_subcircuit(vcc, gnd)

    # Create second voltage divider subcircuit (comment/uncomment to test)
    # Uncomment the line below to add second subcircuit instance
    # Auto-named as "voltage_divider_subcircuit_2"
    # NOTE: Currently blocked by reference collision bug - subcircuits should have independent namespaces
    # vout_2 = voltage_divider_subcircuit(vcc, gnd)

    return vcc, gnd  # Return nets to keep them in scope


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = voltage_divider_instances()

    circuit_obj.generate_kicad_project(
        project_name="voltage_divider_instances",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Hierarchical voltage divider circuit generated successfully!")
    print("📁 Open in KiCad: voltage_divider_instances/voltage_divider_instances.kicad_pro")
    print()
    print("💡 Hierarchical subcircuit duplication demonstrated:")
    print("   - One voltage divider subcircuit created (voltage_divider_subcircuit_1)")
    print("   - Auto-named by calling voltage_divider_subcircuit() function")
    print("   - Appears as hierarchical sheet symbol on parent schematic")
    print("   - Divider circuit exists on its own subsheet")
    print("   - Uncomment line 80 to add second subcircuit instance (voltage_divider_subcircuit_2)")
    print("   - Both subcircuits share VCC and GND nets via hierarchical pins")
    print("   - Each has its own VOUT hierarchical pin")
