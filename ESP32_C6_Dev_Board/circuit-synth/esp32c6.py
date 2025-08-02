#!/usr/bin/env python3
"""
ESP32_C6_MCU Circuit - Converted from KiCad hierarchical sheet
ESP32 MCU with power and USB interface
"""

from circuit_synth import *
from debug_header import debug_header
from led_blinker import led_blinker

@circuit(name="ESP32_C6_MCU")
def esp32c6(vcc_3v3, gnd, usb_dp, usb_dm):
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
    unconnected__u2_io1_pad13_ = Net("unconnected-(U2-IO1-Pad13)")
    unconnected__u2_io2_pad5_ = Net("unconnected-(U2-IO2-Pad5)")
    unconnected__u2_io3_pad6_ = Net("unconnected-(U2-IO3-Pad6)")
    unconnected__u2_io4_pad9_ = Net("unconnected-(U2-IO4-Pad9)")
    unconnected__u2_io5_pad10_ = Net("unconnected-(U2-IO5-Pad10)")
    unconnected__u2_io6_pad15_ = Net("unconnected-(U2-IO6-Pad15)")
    unconnected__u2_io7_pad16_ = Net("unconnected-(U2-IO7-Pad16)")
    unconnected__u2_io9_pad23_ = Net("unconnected-(U2-IO9-Pad23)")
    unconnected__u2_io12_pad17_ = Net("unconnected-(U2-IO12-Pad17)")
    unconnected__u2_io13_pad18_ = Net("unconnected-(U2-IO13-Pad18)")
    unconnected__u2_io14_pad19_ = Net("unconnected-(U2-IO14-Pad19)")
    unconnected__u2_io15_pad20_ = Net("unconnected-(U2-IO15-Pad20)")
    unconnected__u2_io20_pad26_ = Net("unconnected-(U2-IO20-Pad26)")
    unconnected__u2_io21_pad27_ = Net("unconnected-(U2-IO21-Pad27)")
    unconnected__u2_io22_pad28_ = Net("unconnected-(U2-IO22-Pad28)")
    unconnected__u2_io23_pad29_ = Net("unconnected-(U2-IO23-Pad29)")
    unconnected__u2_nc_pad4_ = Net("unconnected-(U2-NC-Pad4)")
    unconnected__u2_nc_pad7_ = Net("unconnected-(U2-NC-Pad7)")
    unconnected__u2_nc_pad21_ = Net("unconnected-(U2-NC-Pad21)")
    unconnected__u2_nc_pad32_ = Net("unconnected-(U2-NC-Pad32)")
    unconnected__u2_nc_pad33_ = Net("unconnected-(U2-NC-Pad33)")
    unconnected__u2_nc_pad34_ = Net("unconnected-(U2-NC-Pad34)")
    unconnected__u2_nc_pad35_ = Net("unconnected-(U2-NC-Pad35)")

    debug_header_circuit = debug_header(vcc_3v3, gnd, debug_tx, debug_rx, debug_en, debug_io0)
    led_blinker_circuit = led_blinker(vcc_3v3, gnd, led_control)


    # Connections
    # TODO: Add component connections based on netlist
    # Example: component1["pin1"] += net_name

