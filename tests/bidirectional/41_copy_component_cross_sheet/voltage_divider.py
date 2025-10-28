#!/usr/bin/env python3
"""
Fixture: Simple voltage divider circuit for testing cross-sheet copy.

This fixture creates a minimal voltage divider that can be:
1. Generated to KiCad
2. Synchronized back to capture positions
3. Copied to another sheet
4. Verified for position preservation

Circuit: VIN -> R1 -> VOUT -> R2 -> GND
"""

from circuit_synth import circuit, Component, Net, Circuit


@circuit(name="voltage_divider")
def voltage_divider():
    """
    Create a simple voltage divider circuit.

    Circuit: VIN -> R1 -> VOUT -> R2 -> GND

    This is the base circuit that will be copied to subcircuit sheets.
    """
    # Create resistors
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

    # Create nets
    vin = Net(name="VIN")
    vout = Net(name="VOUT")
    gnd = Net(name="GND")

    # Connect voltage divider
    vin += r1[1]
    vout += r1[2]
    vout += r2[1]
    gnd += r2[2]


@circuit(name="voltage_divider_with_subcircuit")
def voltage_divider_with_subcircuit():
    """
    Create a circuit with root sheet and empty subcircuit sheet.

    Root sheet: VIN -> R1 -> VOUT -> R2 -> GND
    Subcircuit: (empty, ready for copy-paste)
    """
    from circuit_synth.core.decorators import get_current_circuit

    root = get_current_circuit()

    # Root sheet components (R1-R2 divider)
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

    # Root nets
    vin = Net(name="VIN")
    vout = Net(name="VOUT")
    gnd = Net(name="GND")

    vin += r1[1]
    vout += r1[2]
    vout += r2[1]
    gnd += r2[2]

    # Add empty subcircuit (will be populated by test)
    subcircuit = Circuit("divider_copy")
    root.add_subcircuit(subcircuit)


@circuit(name="voltage_divider_with_copy")
def voltage_divider_with_copy():
    """
    Create circuit with voltage divider copied to subcircuit.

    Root sheet: VIN -> R1 -> VOUT -> R2 -> GND
    Subcircuit: VIN_SUB -> R3 -> VOUT_SUB -> R4 -> GND_SUB
    """
    from circuit_synth.core.decorators import get_current_circuit

    root = get_current_circuit()

    # Root sheet components (R1-R2 divider)
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

    # Root nets
    vin = Net(name="VIN")
    vout = Net(name="VOUT")
    gnd = Net(name="GND")

    vin += r1[1]
    vout += r1[2]
    vout += r2[1]
    gnd += r2[2]

    # Create subcircuit with copied divider
    subcircuit = Circuit("divider_copy")

    # Subcircuit components (R3-R4 divider - copy of R1-R2)
    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r4 = Component(
        symbol="Device:R",
        ref="R4",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Subcircuit nets (independent from root)
    vin_sub = Net(name="VIN_SUB")
    vout_sub = Net(name="VOUT_SUB")
    gnd_sub = Net(name="GND_SUB")

    vin_sub += r3[1]
    vout_sub += r3[2]
    vout_sub += r4[1]
    gnd_sub += r4[2]

    # Add components and nets to subcircuit
    subcircuit.add_component(r3)
    subcircuit.add_component(r4)
    subcircuit.add_net(vin_sub)
    subcircuit.add_net(vout_sub)
    subcircuit.add_net(gnd_sub)

    # Add subcircuit to root
    root.add_subcircuit(subcircuit)


@circuit(name="voltage_divider_with_existing")
def voltage_divider_with_existing():
    """
    Create circuit where subcircuit already has a component.

    Root sheet: VIN -> R1 -> VOUT -> R2 -> GND
    Subcircuit: R5 (existing), then R6-R7 copied divider added

    Tests copying into non-empty sheet.
    """
    from circuit_synth.core.decorators import get_current_circuit

    root = get_current_circuit()

    # Root sheet components (R1-R2 divider)
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

    # Root nets
    vin = Net(name="VIN")
    vout = Net(name="VOUT")
    gnd = Net(name="GND")

    vin += r1[1]
    vout += r1[2]
    vout += r2[1]
    gnd += r2[2]

    # Create subcircuit with existing R5
    subcircuit = Circuit("divider_copy")

    r5 = Component(
        symbol="Device:R",
        ref="R5",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    subcircuit.add_component(r5)

    # Now add copied divider (R6-R7)
    r6 = Component(
        symbol="Device:R",
        ref="R6",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r7 = Component(
        symbol="Device:R",
        ref="R7",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Subcircuit nets for copied divider
    vin_sub = Net(name="VIN_SUB")
    vout_sub = Net(name="VOUT_SUB")
    gnd_sub = Net(name="GND_SUB")

    vin_sub += r6[1]
    vout_sub += r6[2]
    vout_sub += r7[1]
    gnd_sub += r7[2]

    # Add copied divider to subcircuit
    subcircuit.add_component(r6)
    subcircuit.add_component(r7)
    subcircuit.add_net(vin_sub)
    subcircuit.add_net(vout_sub)
    subcircuit.add_net(gnd_sub)

    # Add subcircuit to root
    root.add_subcircuit(subcircuit)


if __name__ == "__main__":
    # Test basic voltage divider
    print("Testing basic voltage divider...")
    circuit_obj = voltage_divider()

    circuit_obj.generate_kicad_project(
        project_name="voltage_divider",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Basic voltage divider circuit generated!")
    print("📁 Open in KiCad: voltage_divider/voltage_divider.kicad_pro")

    # Test with subcircuit and copy
    print("\nTesting voltage divider with copy to subcircuit...")
    circuit_copy = voltage_divider_with_copy()

    circuit_copy.generate_kicad_project(
        project_name="voltage_divider_with_copy",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Voltage divider with copy generated!")
    print("📁 Open in KiCad: voltage_divider_with_copy/voltage_divider_with_copy.kicad_pro")
