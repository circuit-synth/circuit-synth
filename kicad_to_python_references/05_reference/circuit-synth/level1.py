#!/usr/bin/env python3
"""
Level 1 subcircuit for 05_reference

Middle layer in 3-level hierarchy.
Contains level2 subcircuit.
"""

from circuit_synth import *
from level2 import level2_circuit

@circuit(name="level1")
def level1_circuit(VCC, VOUT, GND):
    """Level 1: passes signals to level 2"""
    
    # Just pass through the nets to level 2
    level2_sub = level2_circuit(VCC, VOUT, GND)