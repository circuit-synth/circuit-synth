#!/usr/bin/env python3
"""
Minimal example showing circuit-synth's automatic update detection.
No manual checking needed - just call generate_kicad_project!
"""

from circuit_synth import Component, Net, circuit

@circuit(name="auto_update_demo")
def auto_update_demo():
    """Demo circuit showing automatic update feature"""
    # Simple voltage divider
    R1 = Component("Device:R", ref="R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    R2 = Component("Device:R", ref="R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    
    VCC = Net("VCC")
    GND = Net("GND")
    VOUT = Net("VOUT")
    
    R1[1] += VCC
    R1[2] += VOUT
    R2[1] += VOUT
    R2[2] += GND

if __name__ == "__main__":
    # Create the circuit
    circuit = auto_update_demo()
    
    # This single line handles EVERYTHING:
    # - Creates new project if it doesn't exist
    # - Updates existing project while preserving manual edits
    # - No need to check if project exists!
    circuit.generate_kicad_project("auto_update_demo")  # force_regenerate=False is now the default!
    
    print("\n✨ That's it! Run this script multiple times and see the magic.")