#!/usr/bin/env python3
"""
Test 1: Single Resistor - Position Preservation
The simplest possible test for bidirectional updates.
"""

from circuit_synth import *

@circuit()
def single_resistor():
    """A single resistor between +5V and GND"""
    
    # Create one resistor
    r = Component(
        symbol="Device:R", 
        ref="R1", 
        value="1k",
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    
    # Create nets
    vcc = Net("+5V")
    gnd = Net("GND")
    
    # Connect the resistor
    vcc += r[1]  # Pin 1 to +5V
    r[2] += gnd  # Pin 2 to GND


def main():
    circuit = single_resistor()
    print("Generating single resistor test circuit...")
    
    # Generate JSON to inspect the format
    circuit._generate_hierarchical_json_netlist("01_single_resistor.json")
    print("Generated JSON: 01_single_resistor.json")
    
    # Generate with force_regenerate=False to enable preservation
    circuit.generate_kicad_project("01_single_resistor", force_regenerate=False)
    print("Done! Check 01_single_resistor/01_single_resistor.kicad_sch")
    print("\nTest steps:")
    print("1. Open in KiCad and move the resistor")
    print("2. Save and close KiCad")
    print("3. Run this script again")
    print("4. Open in KiCad - resistor should stay where you moved it")


if __name__ == "__main__":
    main()