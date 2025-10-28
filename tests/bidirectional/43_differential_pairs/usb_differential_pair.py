#!/usr/bin/env python3
"""
Fixture: USB differential pair circuit.

Creates a USB Type B connector and a USB transceiver/buffer component
with differential pair connections (D+ and D-).

This is the foundational differential pair test - validates that
differential pair naming and connections work correctly in KiCad.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="usb_differential_pair")
def usb_differential_pair():
    """Circuit with USB differential pair (D+ and D-)."""

    # USB Type B Micro connector
    # Pin 1: Vcc (5V)
    # Pin 2: D- (Data Minus)
    # Pin 3: D+ (Data Plus)
    # Pin 4: GND
    # Pin 5: ID (for OTG detection, not used here)
    # Pin 6: GND (second ground pin for shield)
    usb_conn = Component(
        symbol="Connector:USB_B_Micro",
        ref="J1",
        value="USB_B_Micro",
        footprint="Connector_USB:USB_Micro-B_Amphenol_10104110-0001LF",
    )

    # Transceiver/buffer IC - using a generic multi-pin connector for demonstration
    # In a real design, this would be a USB transceiver like TUSB1106 or similar
    # Pin 1: Vcc
    # Pin 2: GND
    # Pin 3: Input D+
    # Pin 4: Output D+ (for USB D+)
    # Pin 5: Input D-
    # Pin 6: Output D- (for USB D-)
    # Pins 7-14: Additional control signals
    transceiver = Component(
        symbol="Connector:Conn_01x14_Pin",  # Generic 14-pin connector as transceiver placeholder
        ref="U1",
        value="USB_Transceiver",  # Represents USB transceiver
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x14_P2.54mm_Vertical",
    )

    # USB_DP net: connects D+ from USB connector to transceiver D+ output
    # USB connector pin 3 (D+) → Transceiver pin 4 (Output D+)
    usb_dp_net = Net(name="USB_DP")
    usb_dp_net += usb_conn[3]      # USB connector D+ pin
    usb_dp_net += transceiver[4]   # Transceiver Output D+ pin

    # USB_DM net: connects D- from USB connector to transceiver D- output
    # USB connector pin 2 (D-) → Transceiver pin 6 (Output D-)
    usb_dm_net = Net(name="USB_DM")
    usb_dm_net += usb_conn[2]      # USB connector D- pin
    usb_dm_net += transceiver[6]   # Transceiver Output D- pin

    # Optional: Add GND net (USB pins to transceiver GND pin)
    # Connector pin 2 is typically GND in multi-pin connectors
    gnd_net = Net(name="GND")
    gnd_net += usb_conn[4]         # Primary GND pin (USB)
    gnd_net += usb_conn[6]         # Shield GND pin (USB)
    gnd_net += transceiver[2]      # Transceiver GND pin (pin 2)

    # Optional: Add Vcc net (USB pin 1 to transceiver Vcc)
    # Connector pin 1 is typically Vcc in multi-pin connectors
    # Note: In real design, this would have decoupling capacitors and regulation
    vcc_net = Net(name="VCC")
    vcc_net += usb_conn[1]         # USB Vcc pin
    vcc_net += transceiver[1]      # Transceiver Vcc pin


if __name__ == "__main__":
    circuit_obj = usb_differential_pair()
    circuit_obj.generate_kicad_project(project_name="usb_differential_pair")
    print("✅ USB differential pair circuit generated!")
    print("📁 Open in KiCad: usb_differential_pair/usb_differential_pair.kicad_pro")
    print("\nVerify:")
    print("  - USB_DP net visible on J1 pin 3 and U1 pin 4")
    print("  - USB_DM net visible on J1 pin 2 and U1 pin 6")
    print("  - GND net visible on J1 pins 4,6 and U1 pin 2")
    print("  - VCC net visible on J1 pin 1 and U1 pin 1")
