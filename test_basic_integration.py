#!/usr/bin/env python3
"""
Test basic integration with both Python and Rust backends.
"""

import logging
from pathlib import Path
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)

sys.path.insert(0, 'src')

from circuit_synth import *

@circuit(name="test_basic")
def create_test_circuit():
    """Test circuit for integration."""
    
    # Create basic components
    r1 = Component(symbol="Device:R", ref="R", value="10k")
    c1 = Component(symbol="Device:C", ref="C", value="100nF")
    
    # Create nets
    vcc = Net("VCC")
    gnd = Net("GND")
    
    # Connect components
    r1["1"] += vcc
    r1["2"] += gnd
    c1["1"] += vcc
    c1["2"] += gnd

# Test 1: Create circuit
print("Test 1: Creating circuit...")
circuit = create_test_circuit()
print(f"  ✓ Circuit created: {circuit.name}")
print(f"  ✓ Components: {len(circuit.components)}")
print(f"  ✓ Nets: {len(circuit.nets)}")

# Test 2: Generate JSON
print("\nTest 2: Generating JSON...")
circuit.generate_json_netlist("test_basic.json")
if Path("test_basic.json").exists():
    print(f"  ✓ JSON generated: {Path('test_basic.json').stat().st_size} bytes")
else:
    print("  ✗ JSON generation failed")
    sys.exit(1)

# Test 3: Generate KiCad project (will use Rust if available)
print("\nTest 3: Generating KiCad project...")
try:
    circuit.generate_kicad_project("test_basic_project", generate_pcb=False)
    if Path("test_basic_project").exists():
        files = list(Path("test_basic_project").glob("*.kicad_*"))
        print(f"  ✓ KiCad project generated with {len(files)} files")
        for f in files:
            print(f"    - {f.name}")
    else:
        print("  ✗ KiCad project directory not created")
        sys.exit(1)
except Exception as e:
    print(f"  ✗ KiCad generation failed: {e}")
    sys.exit(1)

print("\n✅ All tests passed!")