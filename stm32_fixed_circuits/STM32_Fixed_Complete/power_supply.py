#!/usr/bin/env python3
"""
STM32 Power Supply Circuit
3.3V power input with filtering and protection
"""

from circuit_synth import *

@circuit(name="STM32_Power_Supply")
def power_supply(vcc_3v3_out, gnd):
    """STM32 power supply subcircuit with filtering"""
    
    # Power input connector (assuming external 3.3V supply)
    power_input = Component(
        symbol="Connector_Generic:Conn_01x02",
        ref="J",
        footprint="Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"
    )
    
    # Power filtering capacitors
    cap_bulk = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    cap_bypass = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Power connections
    power_input[1] += vcc_3v3_out  # 3.3V input
    power_input[2] += gnd          # Ground
    
    # Power filtering
    cap_bulk[1] += vcc_3v3_out
    cap_bulk[2] += gnd
    cap_bypass[1] += vcc_3v3_out
    cap_bypass[2] += gnd
