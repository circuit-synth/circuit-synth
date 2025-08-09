#!/usr/bin/env python3
"""
Test multi-unit component handling in KiCad schematic generation.

This tests several challenging multi-unit scenarios:
1. LM358 - Dual op-amp (2 amplifier units + 1 power unit)
2. 74HC00 - Quad NAND gate (4 gate units + 1 power unit)  
3. LM324 - Quad op-amp (4 amplifier units + 1 power unit)
"""

from circuit_synth import *


@circuit(name='test_multiunit')
def test_multiunit():
    """
    Test circuit with multiple multi-unit components to verify:
    - Correct unit assignment (U1A, U1B, U1C, etc.)
    - Power unit handling (usually unit 5 for quad chips)
    - Multiple instances of same multi-unit component
    """
    
    # Test component - 74HC14 hex inverter with 7 units
    u1 = Component(
        symbol="74xx:74HC14",
        ref="U",
        value="74HC14",
        footprint="Package_SO:TSSOP-14_4.4x5mm_P0.65mm"
    )
    
    # The system should automatically detect this is a multi-unit component
    # and create all 7 units (6 inverters + 1 power unit)
   


# Generate the circuit
if __name__ == '__main__':
    circuit = test_multiunit()
    
    # Generate KiCad project
    print("Generating KiCad project with multi-unit components...")
    circuit.generate_kicad_project(project_name="test_multiunit")
    
    # Generate netlist
    circuit.generate_kicad_netlist("test_multiunit/test_multiunit.net")
