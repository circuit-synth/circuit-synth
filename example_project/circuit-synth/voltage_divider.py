#!/usr/bin/env python3
"""
Voltage Divider Circuit - Basic Analog Design
Simple resistor voltage divider with optional simulation
"""

from circuit_synth import *

@circuit
def voltage_divider():
    """Voltage divider: 5V → 3.3V using resistors"""
    
    # Components - precision resistors for accurate division
    r1 = Component(symbol="Device:R", ref="R", value="1.7k", 
                  footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R", value="3.3k",
                  footprint="Resistor_SMD:R_0603_1608Metric") 
    
    # Nets
    vin = Net("VIN")      # 5V input
    vout = Net("VOUT")    # 3.3V output  
    gnd = Net("GND")      # Ground
    
    # Connections
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd
    
    # Optional: Add simulation analysis
    # To run simulation: circuit.simulator().operating_point()

if __name__ == "__main__":
    circuit = voltage_divider()
    circuit.generate_kicad_project("voltage_divider")
    print("✅ Voltage divider circuit generated!")
    print("🔬 Expected output: 3.28V (from 5V input)")
