#!/usr/bin/env python3
"""
Branch A subcircuit for 06_reference

First branch in complex hierarchical design.
Contains nested divider_a subcircuit.
"""

from circuit_synth import *
from divider_a import divider_a_circuit

@circuit(name="branch_a")
def branch_a_circuit(VCC, VOUT, GND):
    """Branch A: contains nested divider A"""
    
    # Pass signals to nested divider
    divider_a_sub = divider_a_circuit(VCC, VOUT, GND)