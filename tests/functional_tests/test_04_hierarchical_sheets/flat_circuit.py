#!/usr/bin/env python3
"""
Flat Circuit for Test Case 04
This will have hierarchical sheets added in KiCad
"""

from circuit_synth import Component, Net, circuit

@circuit
def root():
    """Create a simple flat circuit"""
    
    # Create nets
    vcc = Net("VCC")
    gnd = Net("GND")
    
    # Add power supply capacitor
    c1 = Component(
        "Device:C",
        ref="C1",
        value="100uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    c1["1"] += vcc
    c1["2"] += gnd
    
    # Add LED with current limiting resistor
    led1 = Component(
        "Device:LED",
        ref="D1",
        value="Red",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    r1 = Component(
        "Device:R",
        ref="R1",
        value="330",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Connect LED circuit
    r1["1"] += vcc
    r1["2"] += led1["1"]  # Anode
    led1["2"] += gnd      # Cathode to ground

if __name__ == "__main__":
    print("Flat circuit for Test 04 generated successfully!")
    print("Components: C1 (100uF), D1 (LED), R1 (330Ω)")
    print("Ready for hierarchical sheet addition in KiCad")