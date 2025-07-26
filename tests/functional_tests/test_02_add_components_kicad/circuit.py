#!/usr/bin/env python3
"""
Initial Single Resistor Circuit for Test Case 02
This will be modified in KiCad and synced back
"""

from circuit_synth import Component, Net, circuit

@circuit
def initial_circuit():
    """Create initial single resistor circuit"""
    
    # Create nets
    vcc = Net("VCC")
    gnd = Net("GND")
    
    # Create and add resistor
    r1 = Component(
        "Device:R",
        ref="R1",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Connect resistor
    r1["1"] += vcc
    r1["2"] += gnd

if __name__ == "__main__":
    print("Initial circuit for Test 02 generated successfully!")