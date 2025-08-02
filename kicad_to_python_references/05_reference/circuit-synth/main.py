#!/usr/bin/env python3
"""
05_reference: 3 nested levels of resistor dividers

This design tests deep hierarchical nesting:
- Main circuit contains level1 subcircuit
- Level1 contains level2 subcircuit  
- Level2 contains the actual resistor divider components
"""

from circuit_synth import *
from level1 import level1_circuit

@circuit(name="05_reference")
def main_circuit():
    """Main circuit with 3-level nested hierarchy"""
    
    # Create global nets
    VCC = Net('VCC')
    GND = Net('GND')
    VOUT = Net('VOUT')
    
    # Instantiate level 1 subcircuit
    level1_sub = level1_circuit(VCC, VOUT, GND)


if __name__ == "__main__":
    print("🚀 Starting 05_reference generation...")
    
    # Generate the complete hierarchical circuit
    circuit = main_circuit()
    
    # Generate KiCad project
    circuit.generate_kicad_project(project_name="05_reference")
    
    print("✅ 05_reference project generated!")