#!/usr/bin/env python3
"""
child2 subcircuit generated from KiCad
"""

from circuit_synth import *

@circuit(name='child2')
def child2():
    """
    child2 subcircuit with LM324 op-amp
    """
    # Create components
    u1 = Component(symbol="Amplifier_Operational:LM324", ref="U", value="LM324")
    
    # Return the circuit
    return locals()