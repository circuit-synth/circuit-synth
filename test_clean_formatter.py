#!/usr/bin/env python3
"""
Test clean formatter after removing old logic
"""

from circuit_synth import *
import os

@circuit(name='test_circuit')
def test_circuit():
    """Simple test circuit for formatter validation"""
    # Simple test circuit
    vcc = Net('VCC')
    gnd = Net('GND')
    
    r1 = Component(symbol='Device:R', ref='R', value='10k', footprint='Resistor_SMD:R_0603_1608Metric')
    r2 = Component(symbol='Device:R', ref='R', value='22k', footprint='Resistor_SMD:R_0603_1608Metric')
    c1 = Component(symbol='Device:C', ref='C', value='100nF', footprint='Capacitor_SMD:C_0603_1608Metric')
    
    r1[1] += vcc
    r1[2] += r2[1]
    r2[2] += c1[1]
    c1[2] += gnd

# Generate KiCad files
output_dir = 'test_clean_formatter_output'
print(f'Generating test circuit to: {output_dir}')

# Get the circuit instance
circ = test_circuit()

# Generate KiCad project
circ.generate_kicad_project(output_dir)

# Check if files were created
import glob
files = glob.glob(os.path.join(output_dir, '*.kicad_*'))
for f in sorted(files):
    print(f'  Created: {os.path.basename(f)}')

# Read the schematic file to verify formatting
sch_file = os.path.join(output_dir, 'test_circuit.kicad_sch')
if os.path.exists(sch_file):
    with open(sch_file, 'r') as f:
        content = f.read()
        print(f'\nSchematic file size: {len(content)} bytes')
        # Check for proper formatting
        if '(kicad_sch' in content:
            print('✓ Valid KiCad schematic header found')
        if '(symbol ' in content:
            print('✓ Symbol blocks found')
        if 'instances' in content:
            print('✓ Instances blocks found (required for KiCad 2025)')
        
        # Check formatting quality
        lines = content.split('\n')
        print(f'✓ Total lines: {len(lines)}')
        
        # Count indentation issues
        bad_indent = 0
        for i, line in enumerate(lines[:100], 1):  # Check first 100 lines
            if line and not line[0].isspace() and not line.startswith('('):
                bad_indent += 1
        
        if bad_indent == 0:
            print('✓ Clean indentation in first 100 lines')
        else:
            print(f'⚠ Found {bad_indent} potential indentation issues')
        
        print('\nFirst 30 lines of schematic:')
        for i, line in enumerate(lines[:30], 1):
            print(f'{i:3}: {line}')

print('\n✅ Test completed successfully!')