#!/usr/bin/env python3
"""
Single Resistor Circuit - Test Case 01
A simple circuit with one 1k resistor between VCC and GND
"""

from circuit_synth import Circuit, Component, Net, circuit

@circuit(name="single_resistor")
def create_single_resistor_circuit():
    """Create a simple single resistor circuit"""
    # Create nets
    abc = Net("abc")  # KiCad sync: Updated net name from VCC to abc
    gnd = Net("GND")
    
    # Create and add resistors
    r1 = Component(
        symbol="Device:R", 
        ref="R1", 
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Connect resistors
    r1["1"] += abc  # KiCad sync: Updated connection from vcc to abc
    r1["2"] += gnd  # Connect pin 2 to GND
    

# IMPORTANT: Create circuit at module level for validation
circuit_instance = create_single_resistor_circuit()

if __name__ == "__main__":
    # Generate KiCad project
    circuit_instance.generate_kicad_project("single_resistor_project", preserve_user_components=False)
    
    print("Single resistor circuit generated successfully!")