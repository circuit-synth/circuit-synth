#!/usr/bin/env python3
"""
child1 subcircuit generated from KiCad
"""

from circuit_synth import *

# Import child circuits
from child2 import child2

@circuit(name='child1')
def child1(gnd):
    """
    child1 subcircuit
    Parameters: GND
    """
    # Create local nets
    netn_p1nvbusnpada4_ = Net('Net-(P1-VBUS-PadA4)')

    # Create components
    p1 = Component(symbol="Connector:USB_C_Plug_USB2.0", ref="P1", value="USB_C_Plug_USB2.0")

    # Instantiate child circuits
    child2_circuit = child2(gnd)

    # Connections
    p1['A1'] += gnd
    p1['A12'] += gnd
    p1['B1'] += gnd
    p1['B12'] += gnd
    p1['S1'] += gnd