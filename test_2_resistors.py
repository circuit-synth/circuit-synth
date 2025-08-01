#!/usr/bin/env python3
"""
Simple 2-resistor voltage divider test circuit to debug PCB generation issues.
This mimics the reference_project structure exactly.
"""

from circuit_synth import *
import logging

# Enable DEBUG logging to see detailed netlist processing
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@circuit(name="test_2_resistors")
def voltage_divider():
    """Simple voltage divider with 2x 10k resistors"""
    
    # Create power nets
    VCC_3V3 = Net('+3.3V')
    GND = Net('GND')
    MID = Net('VOUT')  # Intermediate voltage node
    
    # Create components - exactly like reference
    R1 = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    R2 = Component(
        symbol="Device:R", 
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Make connections - voltage divider topology (no power symbols, just nets like reference)
    # R1: +3.3V to VOUT
    R1[1] += VCC_3V3
    R1[2] += MID
    
    # R2: VOUT to GND  
    R2[1] += MID
    R2[2] += GND

if __name__ == "__main__":
    print("🚀 Starting simple 2-resistor test circuit generation...")
    
    # Generate the circuit
    circuit = voltage_divider()
    
    print("📋 Generating KiCad project...")
    circuit.generate_kicad_project("test_2_resistors", force_regenerate=True)
    
    print("✅ Generation complete! Check test_2_resistors/ directory")