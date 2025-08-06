#!/usr/bin/env python3
"""
Debug_Header subcircuit generated from KiCad
"""

from circuit_synth import *


@circuit(name="Debug_Header")
def debug_header(gnd, vcc_3v3, debug_en, debug_io0, debug_rx, debug_tx):
    """
    Debug_Header subcircuit
    Parameters: GND, VCC_3V3, DEBUG_EN, DEBUG_IO0, DEBUG_RX, DEBUG_TX
    """

    # Create components
    j2 = Component(
        symbol="Connector_Generic:Conn_02x03_Odd_Even",
        ref="J2",
        value="~",
        footprint="Connector_IDC:IDC-Header_2x03_P2.54mm_Vertical",
    )

    # Connections
    j2[1] += debug_en
    j2[6] += debug_io0
    j2[5] += debug_rx
    j2[3] += debug_tx
    j2[4] += gnd
    j2[2] += vcc_3v3
