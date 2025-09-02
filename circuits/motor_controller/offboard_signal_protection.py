#!/usr/bin/env python3
"""
offboard_signal_protection subcircuit generated from KiCad
"""

from circuit_synth import *

@circuit(name='offboard_signal_protection')
def offboard_signal_protection(bemf1, ghs3):
    """
    offboard_signal_protection subcircuit
    Parameters: Motor Controller/BEMF1, Motor Controller/GHS3
    """
    # Create local nets
    netn_d18na_ = Net('Net-(D18-A)')

    # Create components
    tp13 = Component(symbol="Connector:TestPoint", ref="TP13", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.5x1.5mm")
    r46 = Component(symbol="Device:R_Small", ref="R46", value="RC-02W2201FT", footprint="Resistor_SMD:R_0402_1005Metric")

    # Connections
    r46[2] += bemf1
    tp13[1] += ghs3
    r46[1] += netn_d18na_