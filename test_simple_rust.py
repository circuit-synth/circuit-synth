#!/usr/bin/env python3
"""
Test script for simple Rust integration.

This script tests the Rust backend with a simple non-hierarchical circuit.
"""

import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)8s | %(name)s - %(message)s'
)

# Add circuit_synth to path
sys.path.insert(0, 'src')

from circuit_synth import *

@circuit(name="simple_test")
def create_simple_test():
    """Simple test circuit for Rust backend."""
    
    # Add a resistor
    r1 = Component(symbol="Device:R", ref="R", value="10k")
    
    # Add a capacitor
    c1 = Component(symbol="Device:C", ref="C", value="100nF")
    
    # Add an LED
    led1 = Component(symbol="Device:LED", ref="D", value="RED")
    
    # Create nets
    vcc = Net("VCC")
    r1["1"] += vcc
    
    gnd = Net("GND")
    c1["2"] += gnd
    led1["2"] += gnd
    
    sig = Net("LED_CTRL")
    r1["2"] += sig
    c1["1"] += sig
    led1["1"] += sig

# Create the circuit
circuit = create_simple_test()

print(f"Created circuit: {circuit.name}")
print(f"  Components: {len(circuit.components)}")
print(f"  Nets: {len(circuit.nets)}")

# Test direct Rust adapter
from circuit_synth.kicad.rust_adapter import RustSchematicAdapter

adapter = RustSchematicAdapter(circuit)
rust_data = adapter.convert_to_rust_format()

print("\nRust format conversion:")
print(f"  Components: {len(rust_data['components'])}")
print(f"  Nets: {len(rust_data['nets'])}")

# Generate schematic
output_path = "test_rust_simple.kicad_sch"
adapter.generate_schematic(output_path)

if Path(output_path).exists():
    print(f"\n✅ Schematic generated successfully: {output_path}")
    print(f"  File size: {Path(output_path).stat().st_size} bytes")
    
    # Show first few lines
    with open(output_path) as f:
        lines = f.readlines()[:5]
        print("\n  First lines of schematic:")
        for line in lines:
            print(f"    {line.rstrip()}")
else:
    print(f"\n❌ Failed to generate schematic")
    sys.exit(1)