#!/usr/bin/env python3
"""
LED Blinker Circuit - Status LED with current limiting
Simple LED indicator with proper current limiting resistor
"""

from circuit_synth import *


@circuit(name="LED_Blinker")
def led_blinker(led_control, gnd):
    """LED with current limiting resistor - Correct circuit topology"""

    # LED and resistor
    led = Component(
        symbol="Device:LED", ref="D", footprint="LED_SMD:LED_0805_2012Metric"
    )
    resistor = Component(
        symbol="Device:R",
        ref="R",
        value="330",
        footprint="Resistor_SMD:R_0805_2012Metric",
    )

    # Correct connections: GPIO -> Resistor -> LED -> GND
    resistor[1] += led_control  # GPIO controls current
    resistor[2] += led["A"]  # Anode (positive terminal)
    led["K"] += gnd  # Cathode to ground (current return path)
