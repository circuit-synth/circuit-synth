#!/usr/bin/env python3
"""
Power_Supply subcircuit generated from KiCad
"""

from circuit_synth import *


@circuit(name="Power_Supply")
def power_supply(gnd, vbus, vcc_3v3):
    """
    Power_Supply subcircuit
    Parameters: GND, VBUS, VCC_3V3
    """

    # Create components
    c2 = Component(
        symbol="Device:C",
        ref="C2",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )
    c3 = Component(
        symbol="Device:C",
        ref="C3",
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )
    u1 = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U1",
        value="~",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    )

    # Connections
    c2[2] += gnd
    c3[2] += gnd
    u1[1] += gnd
    c2[1] += vbus
    u1[3] += vbus
    c3[1] += vcc_3v3
    u1[2] += vcc_3v3
