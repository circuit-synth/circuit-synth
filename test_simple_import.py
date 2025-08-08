#!/usr/bin/env python3
"""Simple test to verify circuit-synth imports correctly despite Rust warnings."""

import sys
import os

# Set environment to suppress Rust module warnings
os.environ['PYTHONWARNINGS'] = 'ignore'

print("Testing circuit-synth import...")

try:
    import circuit_synth
    print(f"✅ circuit_synth imported successfully, version: {circuit_synth.__version__}")
except Exception as e:
    print(f"❌ Failed to import circuit_synth: {e}")
    sys.exit(1)

print("\nTesting basic circuit creation...")
try:
    from circuit_synth import Circuit, Component, Net
    circuit = Circuit("test")
    r1 = Component(symbol="Device:R", ref="R", value="1k")
    circuit.add_component(r1)
    print("✅ Basic circuit creation successful")
except Exception as e:
    print(f"❌ Circuit creation failed: {e}")
    sys.exit(1)

print("\nTesting JSON netlist generation...")
try:
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    circuit.generate_json_netlist(temp_file)
    
    # Read the generated file to verify it was created
    with open(temp_file, 'r') as f:
        json_content = f.read()
    
    print("✅ JSON netlist generation successful")
    print(f"   Generated {len(json_content)} bytes of JSON")
    
    # Clean up
    import os
    os.unlink(temp_file)
except Exception as e:
    print(f"❌ JSON netlist generation failed: {e}")
    sys.exit(1)

print("\n🎉 All tests passed! Package is ready for PyPI release.")