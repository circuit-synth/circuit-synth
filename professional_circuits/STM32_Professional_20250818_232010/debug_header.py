#!/usr/bin/env python3
"""
SWD Debug Header Circuit
SWD debug and programming interface for STM32
"""

from circuit_synth import *

@circuit(name="SWD_Debug_Header")
def debug_header(vcc_3v3, gnd, swdio, swclk):
    """SWD debug header subcircuit"""
    
    # SWD debug connector (4-pin: VCC, GND, SWDIO, SWCLK)
    swd_conn = Component(
        symbol="Connector_Generic:Conn_01x04",
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
    )
    
    # Connections
    swd_conn[1] += vcc_3v3  # Power
    swd_conn[2] += gnd      # Ground
    swd_conn[3] += swdio    # SWDIO
    swd_conn[4] += swclk    # SWCLK
