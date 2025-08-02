#!/usr/bin/env python3
"""
Branch B subcircuit for 06_reference

Second branch in complex hierarchical design.
Contains nested divider_b subcircuit.
"""

from circuit_synth import *
from divider_b import divider_b_circuit

@circuit(name="branch_b")
def branch_b_circuit(VCC, VOUT, GND):
    """Branch B: contains nested divider B"""
    
    # Pass signals to nested divider
    divider_b_sub = divider_b_circuit(VCC, VOUT, GND)