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
    
    return locals()

def test_preservation():
    """Test the preservation workflow"""
    project_name = "preservation_test"
    project_exists = os.path.exists(f"{project_name}/{project_name}.kicad_pro")
    
    # Create circuit instance
    test_circuit = simple_test()
    
    if not project_exists:
        print("🚀 GENERATING new KiCad project...")
        print("After generation:")
        print("1. Open in KiCad")
        print("2. Move some components around")
        print("3. Add some wires")
        print("4. Save and close KiCad")
        print("5. Run this script again")
        
        test_circuit.generate_kicad_project(project_name, force_regenerate=True)
        print(f"\n✅ Project generated at: {project_name}/")
        print("📝 Now make manual edits in KiCad and run this script again!")
    else:
        print("🔄 UPDATING existing project (preserving manual edits)...")
        print("Your manual component positions and routing should be preserved!")
        
        # Update with preservation
        test_circuit.generate_kicad_project(project_name, force_regenerate=False)
        
        print("\n✅ Project updated!")
        print("🔍 Check that your manual edits were preserved:")
        print("   - Component positions")
        print("   - Wire routing")
        print("   - Any manual annotations")

if __name__ == "__main__":
    test_preservation()