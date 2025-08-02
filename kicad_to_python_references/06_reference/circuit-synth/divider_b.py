#!/usr/bin/env python3
"""
Divider B subcircuit for 06_reference

Bottom level of branch B hierarchy.
Contains actual resistor divider components.
"""

from circuit_synth import *

@circuit(name="divider_b")
def divider_b_circuit(VCC, VOUT, GND):
    """Divider B: 33k/33k resistor divider"""
    
    # Create resistor components for branch B
    r1b = Component(
        symbol="Device:R",
        ref="R",
        value="33k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    r2b = Component(
        symbol="Device:R",
        ref="R",
        value="33k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Connect voltage divider B
    r1b[1] += VCC      # R1B pin 1 to VCC
    r1b[2] += VOUT     # R1B pin 2 to VOUT
    r2b[1] += VOUT     # R2B pin 1 to VOUT
    r2b[2] += GND      # R2B pin 2 to GND