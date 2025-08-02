#!/usr/bin/env python3
"""
Power distribution for 09_reference

Converts 5V input to 3.3V regulated output.
Tests power net naming and distribution.
"""

from circuit_synth import *

@circuit(name="power_distribution")
def power_distribution_circuit(VCC_5V, VCC_3V3, GND):
    """Power distribution: 5V to 3.3V regulation"""
    
    # Linear regulator
    reg = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    # Bulk capacitor
    cap_bulk = Component(
        symbol="Device:C",
        ref="C",
        value="100uF",
        footprint="Capacitor_SMD:C_1210_3225Metric"
    )
    
    # Connect regulator
    reg["VI"] += VCC_5V      # 5V input
    reg["VO"] += VCC_3V3     # 3.3V output
    reg["GND"] += GND        # Ground
    
    # Connect bulk capacitor
    cap_bulk[1] += VCC_3V3   # Bulk cap on 3.3V rail
    cap_bulk[2] += GND