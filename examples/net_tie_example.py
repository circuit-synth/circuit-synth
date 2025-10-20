#!/usr/bin/env python3
"""
Net-Tie Example - Liberal Net-Tie Insertion for Component Grouping

This example demonstrates how to use net-ties to make component relationships
explicit, especially for decoupling capacitors. Net-ties help:

1. Make power distribution topology clear in schematics
2. Guide placement algorithms (components connected via net-tie placed adjacent)
3. Show which decoupling cap serves which power pin

Example topology:
    MCU VDD_CORE → C1 → NetTie1 → VCC
    MCU VDD_IO → C2 → NetTie2 → VCC
    MCU VDDA → C3 → NetTie3 → VCC

Without net-ties, all caps would just connect to VCC, making the relationship unclear.
With net-ties, it's explicit which cap decouples which power domain.
"""

from circuit_synth import Circuit, Component, Net, circuit


@circuit(name="MCU_With_Net_Ties")
def mcu_with_net_ties(VCC_3V3, GND):
    """
    STM32 microcontroller with explicit decoupling using net-ties.

    This circuit demonstrates automatic net-tie insertion for decoupling
    capacitors, making power distribution topology explicit.
    """

    # STM32F411 microcontroller with multiple power domains
    mcu = Component(
        symbol="MCU_ST_STM32F4:STM32F411CEUx",
        ref="U",
        footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm",
        value="STM32F411CEUx"
    )

    # Decoupling capacitors for different power domains
    # Digital core power
    cap_vdd = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Analog power
    cap_vdda = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Bulk capacitor
    cap_bulk = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # Additional bypass cap
    cap_bypass = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Connect MCU power pins
    mcu["VDD"] += VCC_3V3
    mcu["VDDA"] += VCC_3V3
    mcu["VSS"] += GND
    mcu["VSSA"] += GND

    # Connect decoupling capacitors
    # These will have net-ties inserted automatically
    cap_vdd["1"] += VCC_3V3
    cap_vdd["2"] += GND

    cap_vdda["1"] += VCC_3V3
    cap_vdda["2"] += GND

    cap_bulk["1"] += VCC_3V3
    cap_bulk["2"] += GND

    cap_bypass["1"] += VCC_3V3
    cap_bypass["2"] += GND


@circuit(name="Multi_IC_With_Net_Ties")
def multi_ic_with_net_ties():
    """
    Multiple ICs with explicit per-IC decoupling using net-ties.

    This demonstrates how net-ties help organize decoupling for multiple ICs
    on the same power rail.
    """

    # Shared power nets
    vcc = Net("VCC_3V3")
    gnd = Net("GND")

    # First IC - MCU
    mcu = Component(
        symbol="MCU_ST_STM32F4:STM32F411CEUx",
        ref="U",
        footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm",
        value="STM32F411"
    )

    mcu_cap = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Second IC - Voltage regulator
    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
        value="AMS1117-3.3"
    )

    reg_cap_in = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    reg_cap_out = Component(
        symbol="Device:C",
        ref="C",
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # Third IC - USB transceiver
    usb = Component(
        symbol="Interface_USB:CH340C",
        ref="U",
        footprint="Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
        value="CH340C"
    )

    usb_cap = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Connect MCU
    mcu["VDD"] += vcc
    mcu["VSS"] += gnd
    mcu_cap["1"] += vcc
    mcu_cap["2"] += gnd

    # Connect regulator
    regulator["VO"] += vcc
    regulator["GND"] += gnd
    reg_cap_in["1"] += vcc
    reg_cap_in["2"] += gnd
    reg_cap_out["1"] += vcc
    reg_cap_out["2"] += gnd

    # Connect USB
    usb["VCC"] += vcc
    usb["GND"] += gnd
    usb_cap["1"] += vcc
    usb_cap["2"] += gnd

    return Circuit.get_active_circuit()


@circuit(name="Manual_Net_Tie_Example")
def manual_net_tie_example():
    """
    Example showing manual net-tie insertion for custom grouping.

    Sometimes you want to explicitly group components that aren't automatically
    detected as decoupling caps (e.g., filtering caps, timing caps, etc.).
    """

    vcc = Net("VCC_3V3")
    gnd = Net("GND")

    # Create some components
    ic = Component(
        symbol="MCU_ST_STM32F4:STM32F411CEUx",
        ref="U1",
        footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
    )

    # Filtering capacitors that we want to group together
    cap_filter1 = Component(
        symbol="Device:C",
        ref="C1",
        value="1uF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    cap_filter2 = Component(
        symbol="Device:C",
        ref="C2",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Connect IC
    ic["VDD"] += vcc
    ic["VSS"] += gnd

    # Connect filter caps to ground
    cap_filter1["2"] += gnd
    cap_filter2["2"] += gnd

    # Get the circuit
    circuit = Circuit.get_active_circuit()

    # Manually insert net-tie to group the two filter caps together
    # This tells the placement algorithm they should be adjacent
    net_tie = circuit.insert_net_tie(
        cap_filter1, "1",
        cap_filter2, "1",
        vcc
    )

    return circuit


def main():
    """
    Demonstrate net-tie usage and generation.
    """
    print("=" * 70)
    print("Net-Tie Example - Liberal Net-Tie Insertion")
    print("=" * 70)
    print()

    # Example 1: Automatic net-tie insertion
    print("Example 1: MCU with automatic net-tie insertion")
    print("-" * 70)

    vcc = Net("VCC_3V3")
    gnd = Net("GND")

    circuit1 = mcu_with_net_ties(vcc, gnd)

    print(f"Circuit: {circuit1.name}")
    print(f"Components before net-ties: {len(circuit1._component_list)}")

    # Insert net-ties automatically
    net_ties = circuit1.insert_decoupling_net_ties()

    print(f"Net-ties inserted: {len(net_ties)}")
    print(f"Components after net-ties: {len(circuit1._component_list)}")

    if net_ties:
        print("\nNet-tie details:")
        for nt in net_ties:
            grouped = nt._extra_fields.get('groups_with', 'N/A')
            ic = nt._extra_fields.get('associated_ic', 'N/A')
            print(f"  {nt.ref}: groups with {grouped}, associated IC: {ic}")

    # Get groupings for placement
    groups = circuit1.get_net_tie_groups()
    if groups:
        print(f"\nNet-tie groups for placement:")
        for net_tie_ref, grouped_refs in groups.items():
            print(f"  {net_tie_ref}: {', '.join(grouped_refs)}")

    # Generate KiCad project
    print("\nGenerating KiCad project...")
    try:
        circuit1.generate_kicad_project(
            project_name="mcu_with_net_ties",
            generate_pcb=True
        )
        print("✓ Project generated: mcu_with_net_ties/")
    except Exception as e:
        print(f"✗ Generation failed: {e}")

    print()

    # Example 2: Multiple ICs with net-ties
    print("Example 2: Multiple ICs with per-IC decoupling")
    print("-" * 70)

    circuit2 = multi_ic_with_net_ties()

    print(f"Circuit: {circuit2.name}")
    print(f"Components: {len(circuit2._component_list)}")

    # Insert net-ties
    net_ties2 = circuit2.insert_decoupling_net_ties()

    print(f"Net-ties inserted: {len(net_ties2)}")

    # Generate KiCad project
    print("\nGenerating KiCad project...")
    try:
        circuit2.generate_kicad_project(
            project_name="multi_ic_with_net_ties",
            generate_pcb=True
        )
        print("✓ Project generated: multi_ic_with_net_ties/")
    except Exception as e:
        print(f"✗ Generation failed: {e}")

    print()

    # Example 3: Manual net-tie insertion
    print("Example 3: Manual net-tie insertion for custom grouping")
    print("-" * 70)

    circuit3 = manual_net_tie_example()

    print(f"Circuit: {circuit3.name}")
    print(f"Components: {len(circuit3._component_list)}")

    # Get groupings
    groups3 = circuit3.get_net_tie_groups()
    if groups3:
        print(f"Manual net-tie groups:")
        for net_tie_ref, grouped_refs in groups3.items():
            print(f"  {net_tie_ref}: {', '.join(grouped_refs)}")

    # Generate KiCad project
    print("\nGenerating KiCad project...")
    try:
        circuit3.generate_kicad_project(
            project_name="manual_net_tie_example",
            generate_pcb=True
        )
        print("✓ Project generated: manual_net_tie_example/")
    except Exception as e:
        print(f"✗ Generation failed: {e}")

    print()
    print("=" * 70)
    print("Benefits of Net-Ties:")
    print("=" * 70)
    print("""
1. CLEAR SCHEMATICS: Shows which cap decouples which power pin
2. BETTER PLACEMENT: Placement algorithm groups related components
3. EXPLICIT TOPOLOGY: Power distribution is visible in the schematic
4. NO ELECTRICAL IMPACT: Net-ties are zero-ohm connections
5. MANUFACTURING FRIENDLY: Excluded from BOM automatically

Without net-ties:    With net-ties:
  VCC                  VCC
   |                    |
   +--C1--GND          NT1---C1---GND (decouples IC1.VDD)
   |                    |
   +--C2--GND          NT2---C2---GND (decouples IC2.VDD)
   |                    |
   +--IC1.VDD          IC1.VDD
   |
   +--IC2.VDD          IC2.VDD

The schematic on the right makes it immediately clear which capacitor
serves which IC, improving readability and guiding PCB layout.
""")


if __name__ == "__main__":
    main()
