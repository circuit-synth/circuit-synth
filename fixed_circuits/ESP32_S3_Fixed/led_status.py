#!/usr/bin/env python3
"""
Status LED Circuit
Status LED with current limiting resistor
"""

from circuit_synth import *

@circuit(name="Status_LED")
def led_status(vcc_3v3_in, gnd_in, led_control_in):
    """Status LED subcircuit"""
    
    # Use input nets
    vcc_3v3 = vcc_3v3_in
    gnd = gnd_in
    led_control = led_control_in
    
    # Status LED
    led = Component(
        symbol="Device:LED",
        ref="D",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    # Current limiting resistor
    led_resistor = Component(
        symbol="Device:R", 
        ref="R",
        value="220",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Connections
    led_control += led_resistor["1"]
    led_resistor["2"] += led["A"]
    led["K"] += gnd
