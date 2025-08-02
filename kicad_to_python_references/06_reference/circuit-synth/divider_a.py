#!/usr/bin/env python3
"""
Divider A subcircuit for 06_reference

Bottom level of branch A hierarchy.
Contains actual resistor divider components.
"""

from circuit_synth import *

@circuit(name="divider_a")
def divider_a_circuit(VCC, VOUT, GND):
    """Divider A: 15k/15k resistor divider"""
    
    # Create resistor components for branch A
    r1a = Component(
        symbol="Device:R",
        ref="R",
        value="15k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    r2a = Component(
        symbol="Device:R",
        ref="R",
        value="15k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Connect voltage divider A
    r1a[1] += VCC      # R1A pin 1 to VCC
    r1a[2] += VOUT     # R1A pin 2 to VOUT
    r2a[1] += VOUT     # R2A pin 1 to VOUT
    r2a[2] += GND      # R2A pin 2 to GND