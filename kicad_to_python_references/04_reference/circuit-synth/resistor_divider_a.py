#!/usr/bin/env python3
"""
Resistor divider A subcircuit for 04_reference

First of two parallel resistor divider hierarchical sheets.
Uses different resistance values than divider B.
"""

from circuit_synth import *

@circuit(name="resistor_divider_a")
def resistor_divider_a(VCC, VOUT, GND):
    """First resistor divider: 10k/10k ratio"""
    
    # Create components with 'A' suffix for uniqueness
    r1a = Component(
        symbol="Device:R",
        ref="R", 
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    r2a = Component(
        symbol="Device:R",
        ref="R",
        value="10k", 
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Connect voltage divider A
    r1a[1] += VCC     # R1A pin 1 to VCC
    r1a[2] += VOUT    # R1A pin 2 to VOUT_A
    r2a[1] += VOUT    # R2A pin 1 to VOUT_A
    r2a[2] += GND     # R2A pin 2 to GND