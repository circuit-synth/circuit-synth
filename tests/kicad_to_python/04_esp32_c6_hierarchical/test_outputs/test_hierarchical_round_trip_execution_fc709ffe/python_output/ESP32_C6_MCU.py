#!/usr/bin/env python3
"""
ESP32_C6_MCU subcircuit generated from KiCad
"""

# Import child circuits
from Debug_Header import debug_header
from LED_Blinker import led_blinker

from circuit_synth import *


@circuit(name="ESP32_C6_MCU")
def esp32_c6_mcu(gnd, vcc_3v3, usb_dm, usb_dp):
    """
    ESP32_C6_MCU subcircuit
    Parameters: GND, VCC_3V3, USB_DM, USB_DP
    """
    # Create local nets
    debug_en = Net("DEBUG_EN")
    debug_io0 = Net("DEBUG_IO0")
    debug_rx = Net("DEBUG_RX")
    debug_tx = Net("DEBUG_TX")
    led_control = Net("LED_CONTROL")
    usb_dm_mcu = Net("USB_DM_MCU")
    usb_dp_mcu = Net("USB_DP_MCU")

    # Create components
    c4 = Component(
        symbol="Device:C",
        ref="C4",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    r4 = Component(
        symbol="Device:R",
        ref="R4",
        value="22",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r5 = Component(
        symbol="Device:R",
        ref="R5",
        value="22",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    u2 = Component(
        symbol="RF_Module:ESP32-C6-MINI-1",
        ref="U2",
        value="~",
        footprint="RF_Module:ESP32-C6-MINI-1",
    )

    # Instantiate child circuits
    debug_header_circuit = debug_header(
        gnd, vcc_3v3, debug_en, debug_io0, debug_rx, debug_tx
    )
    led_blinker_circuit = led_blinker(gnd, led_control)

    # Connections
    u2[8] += debug_en
    u2[12] += debug_io0
    u2[30] += debug_rx
    u2[31] += debug_tx
    c4[2] += gnd
    u2[1] += gnd
    u2[11] += gnd
    u2[14] += gnd
    u2[2] += gnd
    u2[36] += gnd
    u2[37] += gnd
    u2[38] += gnd
    u2[39] += gnd
    u2[40] += gnd
    u2[41] += gnd
    u2[42] += gnd
    u2[43] += gnd
    u2[44] += gnd
    u2[45] += gnd
    u2[46] += gnd
    u2[47] += gnd
    u2[48] += gnd
    u2[49] += gnd
    u2[50] += gnd
    u2[51] += gnd
    u2[52] += gnd
    u2[53] += gnd
    u2[22] += led_control
    r5[1] += usb_dm
    r5[2] += usb_dm_mcu
    u2[25] += usb_dm_mcu
    r4[1] += usb_dp
    r4[2] += usb_dp_mcu
    u2[24] += usb_dp_mcu
    c4[1] += vcc_3v3
    u2[3] += vcc_3v3
