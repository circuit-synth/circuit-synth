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
    

    

if __name__ == "__main__":
    circuit = create_rc_circuit()
    circuit.generate_kicad_project(
        project_name="single_resistor",)