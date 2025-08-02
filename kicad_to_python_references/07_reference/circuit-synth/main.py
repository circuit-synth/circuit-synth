#!/usr/bin/env python3
"""
07_reference: Mixed components (resistor, capacitor, LED) single level

This design tests component variety in a single hierarchical sheet.
Tests different component types beyond just resistors.
"""

from circuit_synth import *
from mixed_circuit import mixed_components_circuit

@circuit(name="07_reference")
def main_circuit():
    """Main circuit with mixed component types in subcircuit"""
    
    # Create global nets
    VCC = Net('VCC')
    GND = Net('GND')
    LED_ANODE = Net('LED_ANODE')
    
    # Instantiate mixed components subcircuit
    mixed_sub = mixed_components_circuit(VCC, LED_ANODE, GND)


if __name__ == "__main__":
    print("🚀 Starting 07_reference generation...")
    
    # Generate the complete hierarchical circuit
    circuit = main_circuit()
    
    # Generate KiCad project
    circuit.generate_kicad_project(project_name="07_reference")
    
    print("✅ 07_reference project generated!")