#!/usr/bin/env python3
"""
02_reference: resistor divider on first child hierarchy

This is a hierarchical design where the main schematic contains
only hierarchical sheets, and the actual resistor divider circuit
is implemented in a child hierarchy.
"""

from circuit_synth import *
from resistor_divider import resistor_divider

@circuit(name="02_reference")
def main_circuit():
    """Main circuit with hierarchical sheet containing resistor divider"""
    
    # Create global nets that connect to the hierarchical sheet
    VCC = Net('VCC')
    GND = Net('GND') 
    VOUT = Net('VOUT')
    
    # Instantiate the resistor divider subcircuit
    divider_circuit = resistor_divider(VCC, VOUT, GND)


if __name__ == "__main__":
    print("🚀 Starting 02_reference generation...")
    
    # Generate the complete hierarchical circuit
    circuit = main_circuit()
    
    # Generate KiCad project
    circuit.generate_kicad_project(project_name="02_reference")
    
