#!/usr/bin/env python3
"""
Debug_Header Circuit - Converted from KiCad hierarchical sheet
Basic subcircuit with power interface
"""

from circuit_synth import *

@circuit(name="Debug_Header")
def debug_header(vcc_3v3, gnd):
    """Basic subcircuit with power interface"""
    
    # Components
    j2 = Component(
        symbol="Connector_Generic:Conn_02x03_Odd_Even",
        ref="J",
        footprint="Connector_IDC:IDC-Header_2x03_P2.54mm_Vertical",
        value="~",
    )

    # Nets
    _esp32_c6_dev_board_main_debug_en = Net("/ESP32_C6_Dev_Board_Main/DEBUG_EN")
    _esp32_c6_dev_board_main_debug_io0 = Net("/ESP32_C6_Dev_Board_Main/DEBUG_IO0")
    _esp32_c6_dev_board_main_debug_rx = Net("/ESP32_C6_Dev_Board_Main/DEBUG_RX")
    _esp32_c6_dev_board_main_debug_tx = Net("/ESP32_C6_Dev_Board_Main/DEBUG_TX")
    _esp32_c6_dev_board_main_gnd = Net("/ESP32_C6_Dev_Board_Main/GND")
    _esp32_c6_dev_board_main_vcc_3v3 = Net("/ESP32_C6_Dev_Board_Main/VCC_3V3")

    # Connections
    # TODO: Add component connections based on netlist
    # Example: component1["pin1"] += net_name

