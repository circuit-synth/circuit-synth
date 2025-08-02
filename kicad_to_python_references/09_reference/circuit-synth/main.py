#!/usr/bin/env python3
"""
09_reference: Power nets across hierarchy (VCC_3V3, GND distribution)

This design tests power net distribution across multiple hierarchical levels.
Tests how power nets are properly routed through the hierarchy.
"""

from circuit_synth import *
from power_dist import power_distribution_circuit
from load_a import load_a_circuit
from load_b import load_b_circuit

@circuit(name="09_reference")
def main_circuit():
    """Main circuit testing power distribution across hierarchy"""
    
    # Create global power nets
    VCC_3V3 = Net('VCC_3V3')
    GND = Net('GND')
    VCC_5V = Net('VCC_5V')
    
    # Instantiate power distribution and load circuits
    power_dist_sub = power_distribution_circuit(VCC_5V, VCC_3V3, GND)
    load_a_sub = load_a_circuit(VCC_3V3, GND)
    load_b_sub = load_b_circuit(VCC_3V3, GND)


if __name__ == "__main__":
    print("🚀 Starting 09_reference generation...")
    
    # Generate the complete hierarchical circuit
    circuit = main_circuit()
    
    # Generate KiCad project
    circuit.generate_kicad_project(project_name="09_reference")
    
    print("✅ 09_reference project generated!")