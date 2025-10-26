#!/usr/bin/env python3
"""
LED_Blinker subcircuit generated from KiCad
"""

from circuit_synth import *


@circuit(name="LED_Blinker")
def led_blinker(gnd, led_control):
    """
    LED_Blinker subcircuit
    Parameters: GND, LED_CONTROL
    """
    # Create local nets
    n_3 = Net("ESP32_C6_MCU/N$3")

    # Create components
    d3 = Component(
        symbol="Device:LED",
        ref="D3",
        value="~",
        footprint="LED_SMD:LED_0805_2012Metric",
    )
    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="330",
        footprint="Resistor_SMD:R_0805_2012Metric",
    )

    # Connections
    d3[2] += n_3
    r3[2] += n_3
    d3[1] += gnd
    r3[1] += led_control
