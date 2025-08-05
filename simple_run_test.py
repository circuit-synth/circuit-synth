#!/usr/bin/env python3
"""
Simple test to see if the basic example works without logging
"""

import sys
from pathlib import Path

# Add source path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("Testing basic circuit-synth import...")

try:
    import circuit_synth
    print("✓ circuit_synth imported successfully")
    
    from circuit_synth import Circuit, Component, Net
    print("✓ Core classes imported successfully")
    
    # Try creating a simple circuit
    circuit = Circuit("test_circuit")
    print("✓ Circuit created successfully")
    
    # Try creating a component
    resistor = Component(symbol="Device:R", ref="R1", value="10k")
    print("✓ Component created successfully")
    
    print("Basic functionality test passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()