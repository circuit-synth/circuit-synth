"""USB-C Basic Circuit - USB-C Connector with CC Resistors

This example demonstrates:
- USB-C connector implementation
- Configuration Channel (CC) resistors for USB-C
- Basic USB power delivery detection

USB-C Configuration:
- CC1, CC2: Configuration Channel pins (need 5.1kΩ resistors to GND for UFP mode)
- VBUS: Power input from USB-C source
- D+/D-: USB 2.0 differential data lines
- GND: Ground pins (multiple for current handling)

This circuit configures the device as a UFP (Upstream Facing Port / Device mode).
"""
from circuit_synth import Component, Net, circuit


@circuit(name="USB_C_Basic")
def usb_c_basic():
    """Basic USB-C connector circuit with CC resistors

    This circuit provides:
    - USB-C receptacle for power and data
    - CC resistors for UFP (device) mode configuration
    - Standard USB 2.0 connections

    The 5.1kΩ resistors on CC1 and CC2 tell the USB-C source that this is
    a device (UFP) and requests default USB power (5V @ up to 3A).
    """

    # USB-C receptacle connector
    # Using a 16-pin USB 2.0-only connector (simpler than full USB-C)
    usb_conn = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0",
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12"
    )

    # CC resistors - 5.1kΩ for UFP (device) mode
    # These resistors advertise to the host that this is a device
    cc1_resistor = Component(
        symbol="Device:R",
        ref="R",
        value="5.1k",  # 5.1k Ohm - standard value for USB-C UFP
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    cc2_resistor = Component(
        symbol="Device:R",
        ref="R",
        value="5.1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Define nets
    vbus = Net('VBUS')      # USB power (5V from host)
    gnd = Net('GND')        # Ground
    usb_dp = Net('USB_DP')  # USB D+ data line
    usb_dm = Net('USB_DM')  # USB D- data line
    cc1 = Net('CC1')        # Configuration Channel 1
    cc2 = Net('CC2')        # Configuration Channel 2

    # Connect USB-C connector
    usb_conn["VBUS"] += vbus  # Power input
    usb_conn["GND"] += gnd    # Ground (connector has multiple GND pins)
    usb_conn["D+"] += usb_dp  # USB Data+
    usb_conn["D-"] += usb_dm  # USB Data-
    usb_conn["CC1"] += cc1    # Configuration Channel 1
    usb_conn["CC2"] += cc2    # Configuration Channel 2

    # Connect CC resistors (pull CC pins to ground)
    # This configures the device in UFP mode
    cc1_resistor[1] += cc1
    cc1_resistor[2] += gnd

    cc2_resistor[1] += cc2
    cc2_resistor[2] += gnd


if __name__ == '__main__':
    # Generate KiCad project
    circuit_obj = usb_c_basic()

    circuit_obj.generate_kicad_project(
        project_name="usb_c_basic",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )

    print("✅ USB-C basic circuit generated!")
    print("📁 Open in KiCad: usb_c_basic/usb_c_basic.kicad_pro")
    print()
    print("📊 Circuit Features:")
    print("   • USB-C receptacle (USB 2.0)")
    print("   • UFP mode configuration (5.1kΩ CC resistors)")
    print("   • VBUS power input (5V)")
    print("   • USB 2.0 data lines (D+/D-)")
    print()
    print("💡 Next Steps:")
    print("   • Add ESD protection diodes on data lines")
    print("   • Add VBUS filtering capacitor")
    print("   • Connect to microcontroller USB interface")
