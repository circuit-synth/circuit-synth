#!/usr/bin/env python3
"""
vsense_mtr subcircuit generated from KiCad
"""

from circuit_synth import *

@circuit(name='vsense_mtr')
def vsense_mtr(phase_v, netn_d11nk_, rotor_cs_3v3, netn_u1npa15_, netn_u2na7_):
    """
    vsense_mtr subcircuit
    Parameters: Motor Controller/PHASE_V, Net-(D11-K), Motor Controller/ROTOR_CS_3v3, Net-(U1-PA15), Net-(U2-A7)
    """

    # Create components
    r22 = Component(symbol="Device:R_Small", ref="R22", value="33", footprint="Resistor_SMD:R_0201_0603Metric")
    tp6 = Component(symbol="Connector:TestPoint", ref="TP6", value="TestPoint", footprint="TestPoint:TestPoint_Pad_1.0x1.0mm")
    c29 = Component(symbol="Device:C_Small", ref="C29", value="CL05A105KA5NQNC", footprint="Capacitor_SMD:C_0402_1005Metric")

    # Connections
    c29[2] += phase_v
    r22[1] += rotor_cs_3v3
    c29[1] += netn_d11nk_
    tp6[1] += netn_u1npa15_
    r22[2] += netn_u2na7_