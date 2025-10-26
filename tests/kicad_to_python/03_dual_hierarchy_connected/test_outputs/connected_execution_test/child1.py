#!/usr/bin/env python3
"""
child1 subcircuit generated from KiCad
"""

from circuit_synth import *


@circuit(name="child1")
def child1(gnd, vin):
    """
    child1 subcircuit
    Parameters: GND, VIN
    """

    # Create components
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Connections
    r2[2] += gnd
    r2[1] += vin
