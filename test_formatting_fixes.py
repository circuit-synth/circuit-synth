#!/usr/bin/env python3
"""
Test script to verify S-expression formatting fixes.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from circuit_synth.kicad.sch_gen.schematic_writer import SchematicWriter
from circuit_synth.kicad.sch_gen.data_structures import Circuit, Component, Net
from circuit_synth.kicad_api.core.types import Point

def create_simple_circuit():
    """Create a simple test circuit with one resistor."""
    circuit = Circuit("test_formatting")
    
    # Add a simple resistor
    resistor = Component(
        ref="R1",
        symbol_id="Device:R",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    resistor.x = 100.0
    resistor.y = 100.0
    resistor.rotation = 0.0
    circuit.add_component(resistor)
    
    # Add a simple net
    net = Net("VCC")
    net.connections.append(("R1", "1"))
    circuit.nets.append(net)
    
    return circuit

def main():
    print("🧪 Testing S-expression formatting fixes...")
    
    # Create test circuit
    circuit = create_simple_circuit()
    
    # Create schematic writer
    writer = SchematicWriter(
        circuit=circuit,
        circuit_dict={"test_formatting": circuit},
        instance_naming_map={},
        paper_size="A4",
        project_name="test_formatting"
    )
    
    # Generate S-expression
    print("📝 Generating S-expression...")
    schematic_expr = writer.generate_s_expr()
    
    # Write to file
    output_path = "test_formatting_output.kicad_sch"
    print(f"💾 Writing to {output_path}...")
    
    from circuit_synth.kicad.sch_gen.schematic_writer import write_schematic_file
    write_schematic_file(schematic_expr, output_path)
    
    # Check the formatting
    print("🔍 Checking formatting...")
    with open(output_path, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Check specific formatting issues
    issues_found = []
    fixes_verified = []
    
    for i, line in enumerate(lines[:50]):  # Check first 50 lines
        line_num = i + 1
        
        # Check generator_version formatting
        if 'generator_version' in line:
            if '(generator_version "9.0")' in line:
                fixes_verified.append(f"✅ Line {line_num}: generator_version has quotes")
            elif '(generator_version 9.0)' in line:
                issues_found.append(f"❌ Line {line_num}: generator_version missing quotes: {line.strip()}")
        
        # Check paper formatting
        if line.strip().startswith('(paper '):
            if '(paper "A4")' in line:
                fixes_verified.append(f"✅ Line {line_num}: paper has quotes")
            elif '(paper A4)' in line:
                issues_found.append(f"❌ Line {line_num}: paper missing quotes: {line.strip()}")
        
        # Check pin_numbers formatting
        if 'pin_numbers' in line and 'hide' in line:
            if '(pin_numbers (hide yes))' in line or '(hide yes)' in line:
                fixes_verified.append(f"✅ Line {line_num}: pin_numbers uses nested structure")
            elif '(pin_numbers hide)' in line:
                issues_found.append(f"❌ Line {line_num}: pin_numbers uses flat structure: {line.strip()}")
        
        # Check property positions
        if 'property' in line and 'at' in line:
            if '(at 0.0 0.0 0)' in line or '(at 0 0 0)' in line:
                issues_found.append(f"❌ Line {line_num}: property using default position: {line.strip()}")
            elif '(at 2.032 0 90)' in line or '(at -1.778 0 90)' in line:
                fixes_verified.append(f"✅ Line {line_num}: property using proper position")
        
        # Check pin_names offset
        if 'pin_names' in line and 'offset' in line:
            if '(offset 0)' in line:
                fixes_verified.append(f"✅ Line {line_num}: pin_names offset is 0")
            elif '(offset 0.254)' in line:
                issues_found.append(f"❌ Line {line_num}: pin_names offset is 0.254: {line.strip()}")
    
    print("\n📊 FORMATTING CHECK RESULTS:")
    print("=" * 50)
    
    if fixes_verified:
        print("✅ FIXES VERIFIED:")
        for fix in fixes_verified:
            print(f"  {fix}")
    
    if issues_found:
        print("\n❌ ISSUES FOUND:")
        for issue in issues_found:
            print(f"  {issue}")
    else:
        print("\n🎉 NO FORMATTING ISSUES FOUND!")
    
    print(f"\n📄 Full output written to: {output_path}")
    print("🔍 You can manually inspect the file for additional verification.")
    
    return len(issues_found) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)