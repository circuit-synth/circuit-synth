#!/usr/bin/env python3
"""
Debug Header Circuit
UART debug and programming interface
"""

from circuit_synth import *

@circuit(name="Debug_Header")
def debug_header(vcc_3v3_in, gnd_in, debug_tx_in, debug_rx_in):
    """Debug header subcircuit"""
    
    # Use input nets
    vcc_3v3 = vcc_3v3_in
    gnd = gnd_in
    debug_tx = debug_tx_in
    debug_rx = debug_rx_in
    
    # Debug header connector
    debug_conn = Component(
        symbol="Connector_Generic:Conn_01x04",
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
    )
    
    # Connections
    debug_conn[1] += vcc_3v3  # Power
    debug_conn[2] += gnd      # Ground
    debug_conn[3] += debug_tx # UART TX
    debug_conn[4] += debug_rx # UART RX
