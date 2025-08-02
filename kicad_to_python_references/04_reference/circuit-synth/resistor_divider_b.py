#!/usr/bin/env python3
"""
Resistor divider B subcircuit for 04_reference

Second of two parallel resistor divider hierarchical sheets.
Uses different resistance values than divider A.
"""

from circuit_synth import *

@circuit(name="resistor_divider_b")
def resistor_divider_b(VCC, VOUT, GND):
    """Second resistor divider: 20k/20k ratio"""
    
    # Create components with 'B' suffix for uniqueness
    r1b = Component(
        symbol="Device:R",
        ref="R",
        value="20k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    r2b = Component(
        symbol="Device:R",
        ref="R", 
        value="20k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Connect voltage divider B
    r1b[1] += VCC     # R1B pin 1 to VCC
    r1b[2] += VOUT    # R1B pin 2 to VOUT_B
    r2b[1] += VOUT    # R2B pin 1 to VOUT_B
    r2b[2] += GND     # R2B pin 2 to GND