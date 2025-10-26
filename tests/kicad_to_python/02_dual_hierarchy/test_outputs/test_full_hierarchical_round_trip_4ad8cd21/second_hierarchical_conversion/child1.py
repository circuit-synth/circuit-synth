#!/usr/bin/env python3
"""
child1 subcircuit generated from KiCad
"""

from circuit_synth import *


@circuit(name="child1")
def child1():
    """
    child1 subcircuit
    """
    # Create local nets
    unconnectedn_r2npad1_ = Net("unconnected-(R2-Pad1)")
    unconnectedn_r2npad2_ = Net("unconnected-(R2-Pad2)")

    # Create components
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
