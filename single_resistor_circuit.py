#!/usr/bin/env python3
"""
Simple circuit-synth example with a single resistor.
"""

from circuit_synth import Component, Net, circuit

@circuit(name="rc_circuit")
def create_rc_circuit():
    """
    Creates a simple RC circuit with a resistor and capacitor.
    
    This demonstrates text positioning on different component types.
    """
    # Create a 1kΩ resistor
    r1 = Component(
        symbol="Device:R",
        ref="R",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Create a 100nF capacitor
    c1 = Component(
        symbol="Device:C",
        ref="C", 
        value="100n",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Create nets
    net1 = Net('Terminal_1')  # Input
    net2 = Net('RC_Junction') # Connection between R and C
    net3 = Net('Terminal_2')  # Output/Ground
    
    # Connect components: Terminal_1 -> R1 -> C1 -> Terminal_2
    r1[1] += net1
    r1[2] += net2
    c1[1] += net2  
    c1[2] += net3
    
    return None  # circuit decorator handles the return

if __name__ == "__main__":
    circuit = create_rc_circuit()
    circuit.generate_kicad_project(
        project_name="RC_Circuit",)