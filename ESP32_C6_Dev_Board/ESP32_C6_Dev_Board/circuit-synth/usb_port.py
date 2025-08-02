#!/usr/bin/env python3
"""
USB_Port Circuit - Converted from KiCad hierarchical sheet
USB-C port with proper parameter interface
"""

from circuit_synth import *

@circuit(name="USB_Port")
def usb_port(vbus_out, gnd, usb_dp, usb_dm):
    """USB-C port with proper parameter interface"""
    
    # Components
    c1 = Component(
        symbol="Device:C",
        ref="C",
        footprint="Capacitor_SMD:C_0805_2012Metric",
        value="10uF",
    )

    d1 = Component(
        symbol="Diode:ESD5Zxx",
        ref="D",
        footprint="Diode_SMD:D_SOD-523",
        value="~",
    )

    d2 = Component(
        symbol="Diode:ESD5Zxx",
        ref="D",
        footprint="Diode_SMD:D_SOD-523",
        value="~",
    )

    j1 = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P",
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
        value="~",
    )

    r1 = Component(
        symbol="Device:R",
        ref="R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="5.1k",
    )

    r2 = Component(
        symbol="Device:R",
        ref="R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="5.1k",
    )

    # Nets
    _esp32_c6_dev_board_main_gnd = Net("/ESP32_C6_Dev_Board_Main/GND")
    _esp32_c6_dev_board_main_n$1 = Net("/ESP32_C6_Dev_Board_Main/N$1")
    _esp32_c6_dev_board_main_n$2 = Net("/ESP32_C6_Dev_Board_Main/N$2")
    _esp32_c6_dev_board_main_usb_dm = Net("/ESP32_C6_Dev_Board_Main/USB_DM")
    _esp32_c6_dev_board_main_usb_dp = Net("/ESP32_C6_Dev_Board_Main/USB_DP")
    _esp32_c6_dev_board_main_vbus = Net("/ESP32_C6_Dev_Board_Main/VBUS")
    unconnected_(j1_d+_padb6) = Net("unconnected-(J1-D+-PadB6)")
    unconnected_(j1_d__padb7) = Net("unconnected-(J1-D--PadB7)")
    unconnected_(j1_sbu1_pada8) = Net("unconnected-(J1-SBU1-PadA8)")
    unconnected_(j1_sbu2_padb8) = Net("unconnected-(J1-SBU2-PadB8)")

    # Connections
    # TODO: Add component connections based on netlist
    # Example: component1["pin1"] += net_name

