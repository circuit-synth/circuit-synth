#!/usr/bin/env python3
"""
Two Resistor Series Circuit for Test Case 03
Tests connection changes between series and parallel configurations
"""

from circuit_synth import Component, Net, circuit

@circuit
def series_resistors():
    """Create two resistors in series configuration"""
    
    # Create nets
    vcc = Net("VCC")
    out = Net("OUT")  # Intermediate net for series connection
    gnd = Net("GND")
    
    # Create and add resistors
    r1 = Component(
        "Device:R",
        ref="R1",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    r2 = Component(
        "Device:R",
        ref="R2",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Connect in series: VCC -> R1 -> OUT -> R2 -> GND
    r1["1"] += vcc
    r1["2"] += out
    r2["1"] += out
    r2["2"] += gnd

if __name__ == "__main__":
    print("Series resistor circuit for Test 03 generated successfully!")
    print("R1: VCC -> OUT")
    print("R2: OUT -> GND")