#!/usr/bin/env python3
"""
Test script for bidirectional KiCad preservation workflow.
This script helps you test the preservation of manual KiCad edits.
"""

import os
import sys
from circuit_synth import Circuit, Component, Net, circuit

@circuit(name="simple_test")
def simple_test():
    """Simple test circuit for preservation testing"""
    # Create some components
    R1 = Component("Device:R", ref="R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    R2 = Component("Device:R", ref="R", value="1k", footprint="Resistor_SMD:R_0603_1608Metric")
    C1 = Component("Device:C", ref="C", value="100nF", footprint="Capacitor_SMD:C_0603_1608Metric")
    
    # Create nets
    VCC = Net("VCC")
    GND = Net("GND")
    SIG = Net("SIGNAL")
    
    # Connect components
    R1[1] += VCC
    R1[2] += SIG
    R2[1] += SIG
    R2[2] += GND
    C1[1] += SIG
    C1[2] += GND
    

def test_preservation():
    """Test the preservation workflow"""
    project_name = "preservation_test"
    
    # Create circuit instance
    test_circuit = simple_test()
    
    print("🚀 Running circuit-synth with automatic update detection...")
    print("\nThe system will automatically:")
    print("  - Create a new project if none exists")
    print("  - Update existing project while preserving manual edits")
    print("")
    
    # Let circuit-synth handle the detection automatically!
    # The default behavior now preserves existing work
    test_circuit.generate_kicad_project(project_name)
    
    # Check if this was first run or update
    if os.path.exists(f"{project_name}/{project_name}.kicad_pro"):
        print("\n✅ Done! The project is at: {}/".format(project_name))
        print("\n📝 Next steps:")
        print("1. Open the project in KiCad")
        print("2. Make manual edits (move components, add wires, etc.)")
        print("3. Save and close KiCad")
        print("4. Run this script again to see preservation in action!")

if __name__ == "__main__":
    test_preservation()