#!/usr/bin/env python3
"""
Power Systems Example - Buck and Boost Converters
Demonstrates different power conversion scenarios using buck and boost patterns
"""

from circuit_synth import *

# Import power conversion patterns
from buck_converter import buck_converter
from boost_converter import boost_converter

@circuit(name="Multi_Rail_Power_System")
def multi_rail_power():
    """
    Multi-output power system with buck and boost converters

    Input: 12V (automotive/industrial)
    Outputs:
    - 5V @ 3A (buck from 12V)
    - 3.3V @ 2A (buck from 5V)
    - 12V @ 500mA (boost from 5V for legacy peripherals)
    """

    # Power rails
    vin_12v = Net('VIN_12V')
    vout_5v = Net('VOUT_5V')
    vout_3v3 = Net('VOUT_3V3')
    vout_12v_boost = Net('VOUT_12V_BOOST')
    gnd = Net('GND')

    # Primary buck: 12V -> 5V @ 3A
    buck_converter(vin_12v, vout_5v, gnd, output_voltage="5V", max_current="3A")

    # Secondary buck: 5V -> 3.3V @ 2A
    # (Could also buck directly from 12V, but cascading is more efficient here)
    buck_converter(vout_5v, vout_3v3, gnd, output_voltage="3.3V", max_current="2A")

    # Boost converter: 5V -> 12V @ 500mA for legacy 12V peripherals
    boost_converter(vout_5v, vout_12v_boost, gnd, output_voltage="12V", max_current="500mA")


@circuit(name="Battery_USB_Power_System")
def battery_usb_power():
    """
    Battery-powered system with USB output

    Input: Single Li-ion cell (3.0V-4.2V)
    Output: 5V USB @ 1A (boost converter)

    Application: Power bank, USB charging from battery
    """

    battery = Net('VBAT')
    usb_5v = Net('USB_5V')
    gnd = Net('GND')

    # Boost 3.7V battery to 5V USB
    boost_converter(battery, usb_5v, gnd, output_voltage="5V", max_current="1A")

    # USB connector
    usb_out = Component(
        symbol="Connector:USB_A",
        ref="J",
        footprint="Connector_USB:USB_A_Stewart_SS-52100-001_Horizontal"
    )
    usb_out["VBUS"] += usb_5v
    usb_out["GND"] += gnd
    # D+/D- would need data logic for proper USB (not shown in power example)


if __name__ == "__main__":
    print("⚡ Power Systems Example Generator")
    print("")
    print("Select example:")
    print("1. Multi-rail power system (12V -> 5V, 3.3V, and boost back to 12V)")
    print("2. Battery USB power bank (3.7V -> 5V)")
    print("")

    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "1":
        print("\n🔌 Generating Multi-Rail Power System...")
        circuit = multi_rail_power()
        name = "Multi_Rail_Power_System"
    elif choice == "2":
        print("\n🔋 Generating Battery USB Power System...")
        circuit = battery_usb_power()
        name = "Battery_USB_Power"
    else:
        print("Invalid choice, generating multi-rail system by default")
        circuit = multi_rail_power()
        name = "Multi_Rail_Power_System"

    circuit.generate_kicad_project(
        project_name=name,
        placement_algorithm="hierarchical",
        generate_pcb=True
    )

    print(f"\n✅ {name} generated!")
    print(f"📁 Check the {name}/ directory for KiCad files")
