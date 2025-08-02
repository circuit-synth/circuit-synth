#!/usr/bin/env python3
"""
Mixed components subcircuit for 07_reference

Contains different component types:
- Resistor (current limiting)
- Capacitor (filtering)  
- LED (indicator)
"""

from circuit_synth import *

@circuit(name="mixed_components")
def mixed_components_circuit(VCC, LED_ANODE, GND):
    """Mixed components: resistor + capacitor + LED circuit"""
    
    # Current limiting resistor
    r1 = Component(
        symbol="Device:R",
        ref="R",
        value="330",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Filter capacitor
    c1 = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # LED indicator
    led1 = Component(
        symbol="Device:LED",
        ref="D",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    # Create intermediate net
    FILTERED_VCC = Net('FILTERED_VCC')
    
    # Connect components
    # Power filtering
    c1[1] += VCC           # C1 positive to VCC
    c1[2] += GND           # C1 negative to GND
    
    # LED current limiting
    r1[1] += VCC           # R1 pin 1 to VCC
    r1[2] += FILTERED_VCC  # R1 pin 2 to filtered supply
    
    # LED connection
    led1["A"] += FILTERED_VCC  # LED anode to filtered supply
    led1["K"] += LED_ANODE     # LED cathode to output net