#!/usr/bin/env python3
"""
Resistor divider subcircuit for 02_reference

This subcircuit implements a simple voltage divider using two resistors.
In KiCad, this would be implemented as a hierarchical sheet.
"""

from circuit_synth import *

@circuit(name="resistor_divider")  
def resistor_divider(VCC, VOUT, GND):
    """Resistor divider circuit: VCC -> R1 -> VOUT -> R2 -> GND"""
    
    # Create components
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
    
    # Connect components to form voltage divider
    r1[1] += VCC      # R1 pin 1 to VCC
    r1[2] += VOUT     # R1 pin 2 to VOUT (middle node)
    r2[1] += VOUT     # R2 pin 1 to VOUT (middle node)  
    r2[2] += GND      # R2 pin 2 to GND