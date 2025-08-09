#!/usr/bin/env python3
"""
child1 subcircuit generated from KiCad
"""

from circuit_synth import *

@circuit(name='child1')
def child1(gnd):
    """
    child1 subcircuit
    Parameters: GND
    """
    
    # Create components
    p1 = Component(symbol="Connector:USB_C_Plug_USB2.0", ref="P1", value="USB_C_Plug_USB2.0")

    # Connections
    p1['A1'] += gnd
    p1['A12'] += gnd
    p1['B1'] += gnd
    p1['B12'] += gnd
    p1['S1'] += gnd