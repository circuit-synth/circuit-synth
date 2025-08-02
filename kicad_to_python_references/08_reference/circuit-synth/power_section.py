#!/usr/bin/env python3
"""
Power section for 08_reference

Simple 5V to 3.3V regulation with decoupling capacitors.
"""

from circuit_synth import *

@circuit(name="power_section")
def power_circuit(VCC_5V, VCC_3V3, GND):
    """Power regulation: 5V to 3.3V with decoupling"""
    
    # 3.3V linear regulator
    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    # Input capacitor
    cap_in = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Output capacitor
    cap_out = Component(
        symbol="Device:C", 
        ref="C",
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Connect regulator
    regulator["VI"] += VCC_5V     # Input voltage
    regulator["VO"] += VCC_3V3    # Output voltage  
    regulator["GND"] += GND       # Ground
    
    # Connect input capacitor
    cap_in[1] += VCC_5V
    cap_in[2] += GND
    
    # Connect output capacitor
    cap_out[1] += VCC_3V3
    cap_out[2] += GND