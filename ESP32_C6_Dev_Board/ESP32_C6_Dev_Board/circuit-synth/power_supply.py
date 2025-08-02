#!/usr/bin/env python3
"""
Power_Supply Circuit - Converted from KiCad hierarchical sheet
Power supply with input/output interface
"""

from circuit_synth import *

@circuit(name="Power_Supply")
def power_supply(vbus_in, vcc_3v3_out, gnd):
    """Power supply with input/output interface"""
    
    # Components
    c2 = Component(
        symbol="Device:C",
        ref="C",
        footprint="Capacitor_SMD:C_0805_2012Metric",
        value="10uF",
    )

    c3 = Component(
        symbol="Device:C",
        ref="C",
        footprint="Capacitor_SMD:C_0805_2012Metric",
        value="22uF",
    )

    u1 = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
        value="~",
    )

    # Nets
    _esp32_c6_dev_board_main_gnd = Net("/ESP32_C6_Dev_Board_Main/GND")
    _esp32_c6_dev_board_main_vbus = Net("/ESP32_C6_Dev_Board_Main/VBUS")
    _esp32_c6_dev_board_main_vcc_3v3 = Net("/ESP32_C6_Dev_Board_Main/VCC_3V3")

    # Connections
    # TODO: Add component connections based on netlist
    # Example: component1["pin1"] += net_name

