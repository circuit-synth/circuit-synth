#!/usr/bin/env python3
"""
06_reference: 3 nested levels of resistor dividers in 2 separate branches

This design tests complex hierarchical branching:
- Main circuit contains branch_a and branch_b
- Each branch contains its own 2-level nested hierarchy
- Tests both depth and breadth of hierarchy
"""

from circuit_synth import *
from branch_a import branch_a_circuit
from branch_b import branch_b_circuit

@circuit(name="06_reference")
def main_circuit():
    """Main circuit with 2 branches, each having 3-level nested hierarchy"""
    
    # Create global nets
    VCC = Net('VCC')
    GND = Net('GND')
    VOUT_A = Net('VOUT_A')
    VOUT_B = Net('VOUT_B')
    
    # Instantiate both branch subcircuits
    branch_a_sub = branch_a_circuit(VCC, VOUT_A, GND)
    branch_b_sub = branch_b_circuit(VCC, VOUT_B, GND)


if __name__ == "__main__":
    print("🚀 Starting 06_reference generation...")
    
    # Generate the complete hierarchical circuit
    circuit = main_circuit()
    
    # Generate KiCad project
    circuit.generate_kicad_project(project_name="06_reference")
    
    print("✅ 06_reference project generated!")