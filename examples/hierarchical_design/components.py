#!/usr/bin/env python3
"""
Component definitions for reusable circuit elements.

This file contains standard component definitions that can be reused
across multiple circuit designs, following software engineering best practices.
"""

from circuit_synth import Component

# Standard SMD resistors - 0603 package
R_1K = Component(
    symbol="Device:R",
    ref="R",
    value="1K",
    footprint="Resistor_SMD:R_0603_1608Metric"
)

R_10K = Component(
    symbol="Device:R", 
    ref="R",
    value="10K",
    footprint="Resistor_SMD:R_0603_1608Metric"
)

R_330 = Component(
    symbol="Device:R",
    ref="R", 
    value="330",
    footprint="Resistor_SMD:R_0603_1608Metric"
)

# Standard SMD capacitors
C_100nF = Component(
    symbol="Device:C",
    ref="C",
    value="100nF", 
    footprint="Capacitor_SMD:C_0603_1608Metric"
)

C_10uF = Component(
    symbol="Device:C",
    ref="C", 
    value="10uF",
    footprint="Capacitor_SMD:C_0805_2012Metric"
)

# Standard LEDs
LED_RED = Component(
    symbol="Device:LED",
    ref="D",
    value="Red", 
    footprint="LED_SMD:LED_0603_1608Metric"
)

LED_GREEN = Component(
    symbol="Device:LED",
    ref="D",
    value="Green",
    footprint="LED_SMD:LED_0603_1608Metric"
)