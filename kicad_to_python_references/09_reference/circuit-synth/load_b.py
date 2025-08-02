#!/usr/bin/env python3
"""
Load B circuit for 09_reference

Second load circuit that consumes power from 3.3V rail.
Tests power net distribution to multiple subcircuits.
"""

from circuit_synth import *

@circuit(name="load_b")
def load_b_circuit(VCC_3V3, GND):
    """Load B: different resistive load with filtering"""
    
    # Load resistor (different value)
    r_load = Component(
        symbol="Device:R",
        ref="R",
        value="2.2k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Filter capacitor
    cap_filter = Component(
        symbol="Device:C",
        ref="C",
        value="1uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Connect load
    r_load[1] += VCC_3V3     # Load connected to 3.3V
    r_load[2] += GND         # Load return to ground
    
    # Connect filter
    cap_filter[1] += VCC_3V3
    cap_filter[2] += GND