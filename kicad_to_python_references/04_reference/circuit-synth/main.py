#!/usr/bin/env python3
"""
04_reference: resistor divider on first child hierarchy and second child hierarchy

This design has two separate hierarchical sheets, each containing
its own resistor divider circuit. Tests multiple parallel hierarchies.
"""

from circuit_synth import *
from resistor_divider_a import resistor_divider_a
from resistor_divider_b import resistor_divider_b

@circuit(name="04_reference")
def main_circuit():
    """Main circuit with two parallel hierarchical sheets, each with resistor dividers"""
    
    # Create global power nets
    VCC = Net('VCC')
    GND = Net('GND')
    
    # Create separate output nets for each divider
    VOUT_A = Net('VOUT_A')
    VOUT_B = Net('VOUT_B')
    
    # Instantiate first resistor divider subcircuit
    divider_a_circuit = resistor_divider_a(VCC, VOUT_A, GND)
    
    # Instantiate second resistor divider subcircuit  
    divider_b_circuit = resistor_divider_b(VCC, VOUT_B, GND)


if __name__ == "__main__":
    print("🚀 Starting 04_reference generation...")
    
    # Generate the complete hierarchical circuit
    circuit = main_circuit()
    
    # Generate KiCad project
    circuit.generate_kicad_project(project_name="04_reference")
    
    print("✅ 04_reference project generated!")