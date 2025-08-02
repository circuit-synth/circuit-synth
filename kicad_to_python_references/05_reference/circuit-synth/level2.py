#!/usr/bin/env python3
"""
Level 2 subcircuit for 05_reference

Bottom layer in 3-level hierarchy.
Contains the actual resistor divider components.
"""

from circuit_synth import *

@circuit(name="level2")
def level2_circuit(VCC, VOUT, GND):
    """Level 2: actual resistor divider implementation"""
    
    # Create resistor components
    r1 = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    r2 = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Connect voltage divider
    r1[1] += VCC      # R1 pin 1 to VCC
    r1[2] += VOUT     # R1 pin 2 to VOUT
    r2[1] += VOUT     # R2 pin 1 to VOUT
    r2[2] += GND      # R2 pin 2 to GND