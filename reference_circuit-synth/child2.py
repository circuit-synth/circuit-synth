#!/usr/bin/env python3
"""
child2 subcircuit generated from KiCad
"""

from circuit_synth import *

@circuit(name='child2')
def child2(gnd):
    """
    child2 subcircuit
    Parameters: GND
    """

    # Create components
    u1 = Component(symbol="Amplifier_Operational:LM324", ref="U1", value="LM324")

    # Connections
    u1[11] += gnd