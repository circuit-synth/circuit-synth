#!/usr/bin/env python3
"""
ESP32_C6_MCU Circuit - Converted from KiCad hierarchical sheet
ESP32 MCU with power and USB interface
"""

from circuit_synth import *

@circuit(name="ESP32_C6_MCU")
def esp32_c6_mcu(vcc_3v3, gnd, usb_dp, usb_dm):
    """ESP32 MCU with power and USB interface"""
    
    # Components
    c4 = Component(
        symbol="Device:C",
        ref="C",
        footprint="Capacitor_SMD:C_0603_1608Metric",
        value="100nF",
    )

    r4 = Component(
        symbol="Device:R",
        ref="R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="22",
    )

    r5 = Component(
        symbol="Device:R",
        ref="R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="22",
    )

    u2 = Component(
        symbol="RF_Module:ESP32-C6-MINI-1",
        ref="U",
        footprint="RF_Module:ESP32-C6-MINI-1",
        value="~",
    )

    # Nets
    _esp32_c6_dev_board_main_debug_en = Net("/ESP32_C6_Dev_Board_Main/DEBUG_EN")
    _esp32_c6_dev_board_main_debug_io0 = Net("/ESP32_C6_Dev_Board_Main/DEBUG_IO0")
    _esp32_c6_dev_board_main_debug_rx = Net("/ESP32_C6_Dev_Board_Main/DEBUG_RX")
    _esp32_c6_dev_board_main_debug_tx = Net("/ESP32_C6_Dev_Board_Main/DEBUG_TX")
    _esp32_c6_dev_board_main_gnd = Net("/ESP32_C6_Dev_Board_Main/GND")
    _esp32_c6_dev_board_main_led_control = Net("/ESP32_C6_Dev_Board_Main/LED_CONTROL")
    _esp32_c6_dev_board_main_usb_dm = Net("/ESP32_C6_Dev_Board_Main/USB_DM")
    _esp32_c6_dev_board_main_usb_dm_mcu = Net("/ESP32_C6_Dev_Board_Main/USB_DM_MCU")
    _esp32_c6_dev_board_main_usb_dp = Net("/ESP32_C6_Dev_Board_Main/USB_DP")
    _esp32_c6_dev_board_main_usb_dp_mcu = Net("/ESP32_C6_Dev_Board_Main/USB_DP_MCU")
    _esp32_c6_dev_board_main_vcc_3v3 = Net("/ESP32_C6_Dev_Board_Main/VCC_3V3")
    unconnected_(u2_io1_pad13) = Net("unconnected-(U2-IO1-Pad13)")
    unconnected_(u2_io2_pad5) = Net("unconnected-(U2-IO2-Pad5)")
    unconnected_(u2_io3_pad6) = Net("unconnected-(U2-IO3-Pad6)")
    unconnected_(u2_io4_pad9) = Net("unconnected-(U2-IO4-Pad9)")
    unconnected_(u2_io5_pad10) = Net("unconnected-(U2-IO5-Pad10)")
    unconnected_(u2_io6_pad15) = Net("unconnected-(U2-IO6-Pad15)")
    unconnected_(u2_io7_pad16) = Net("unconnected-(U2-IO7-Pad16)")
    unconnected_(u2_io9_pad23) = Net("unconnected-(U2-IO9-Pad23)")
    unconnected_(u2_io12_pad17) = Net("unconnected-(U2-IO12-Pad17)")
    unconnected_(u2_io13_pad18) = Net("unconnected-(U2-IO13-Pad18)")
    unconnected_(u2_io14_pad19) = Net("unconnected-(U2-IO14-Pad19)")
    unconnected_(u2_io15_pad20) = Net("unconnected-(U2-IO15-Pad20)")
    unconnected_(u2_io20_pad26) = Net("unconnected-(U2-IO20-Pad26)")
    unconnected_(u2_io21_pad27) = Net("unconnected-(U2-IO21-Pad27)")
    unconnected_(u2_io22_pad28) = Net("unconnected-(U2-IO22-Pad28)")
    unconnected_(u2_io23_pad29) = Net("unconnected-(U2-IO23-Pad29)")
    unconnected_(u2_nc_pad4) = Net("unconnected-(U2-NC-Pad4)")
    unconnected_(u2_nc_pad7) = Net("unconnected-(U2-NC-Pad7)")
    unconnected_(u2_nc_pad21) = Net("unconnected-(U2-NC-Pad21)")
    unconnected_(u2_nc_pad32) = Net("unconnected-(U2-NC-Pad32)")
    unconnected_(u2_nc_pad33) = Net("unconnected-(U2-NC-Pad33)")
    unconnected_(u2_nc_pad34) = Net("unconnected-(U2-NC-Pad34)")
    unconnected_(u2_nc_pad35) = Net("unconnected-(U2-NC-Pad35)")

    # Connections
    # TODO: Add component connections based on netlist
    # Example: component1["pin1"] += net_name

