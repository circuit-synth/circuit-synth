#!/usr/bin/env python3
"""
Power Supply Circuit - 5V to 3.3V regulation
Clean power regulation from USB-C VBUS to regulated 3.3V
"""

from circuit_synth import *

@circuit(name="Power_Supply")
def power_supply(vbus_in, gnd_in):
    """5V to 3.3V power regulation subcircuit"""
    
    # Create output nets
    vcc_3v3 = Net('VCC_3V3')
    gnd = gnd_in  # Use input ground
    
    # 3.3V regulator
    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3", 
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    # Input/output capacitors
    cap_in = Component(
        symbol="Device:C", 
        ref="C", 
        value="10uF", 
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    cap_out = Component(
        symbol="Device:C", 
        ref="C", 
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Connections
    regulator["VI"] += vbus_in
    regulator["VO"] += vcc_3v3 
    regulator["GND"] += gnd
    
    cap_in["1"] += vbus_in
    cap_in["2"] += gnd
    cap_out["1"] += vcc_3v3
    cap_out["2"] += gnd
    
    return vcc_3v3, gnd
