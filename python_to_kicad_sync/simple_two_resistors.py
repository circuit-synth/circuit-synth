#!/usr/bin/env python3
"""
Simple Two Resistor Circuit

A minimal circuit-synth example with just two resistors.
This will be used to test surgical operations integration.
"""

from circuit_synth import *

@circuit(name="simple_two_resistors")
def simple_two_resistors():
    """Simple circuit with two resistors for testing surgical operations."""
    
    # Start with minimal circuit - single resistor that we'll modify surgically
    r1 = Component(
        symbol="Device:R",
        ref="R", 
        value="1k",
        footprint="Resistor_SMD:R_0402_1005Metric"
    )
    
    
    # # Additional resistors to be added surgically:
    # r2 = Component(
    #     symbol="Device:R", 
    #     ref="R",
    #     value="22k",
    #     footprint="Resistor_SMD:R_0805_2012Metric"
    # )

if __name__ == "__main__":
    print("🔧 Generating simple two resistor circuit...")
    
    # Generate the circuit
    circuit = simple_two_resistors()
    
    circuit.generate_kicad_project(
        project_name="simple_two_resistors",
        force_regenerate=True,
        generate_pcb=False
    )