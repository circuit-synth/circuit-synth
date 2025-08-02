#!/usr/bin/env python3
"""
Load A circuit for 09_reference

First load circuit that consumes power from 3.3V rail.
Tests power net distribution to subcircuits.
"""

from circuit_synth import *

@circuit(name="load_a")
def load_a_circuit(VCC_3V3, GND):
    """Load A: resistive load with decoupling"""
    
    # Load resistor
    r_load = Component(
        symbol="Device:R",
        ref="R",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Decoupling capacitor
    cap_decouple = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Connect load
    r_load[1] += VCC_3V3     # Load connected to 3.3V
    r_load[2] += GND         # Load return to ground
    
    # Connect decoupling
    cap_decouple[1] += VCC_3V3
    cap_decouple[2] += GND