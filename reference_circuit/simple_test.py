#!/usr/bin/env python3
"""
Simple test: Generate 3 circuits and compare to reference.
"""

import sys
from pathlib import Path
import difflib

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from circuit_synth import *


@circuit(name="blank_schematic")
def blank_schematic():
    """A blank schematic circuit."""
    pass


@circuit(name="single_resistor")
def single_resistor():
    """A circuit with a single 10k resistor."""
    r1 = Component("Device:R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    return r1


@circuit(name="two_resistors") 
def two_resistors():
    """A circuit with two 10k resistors."""
    r1 = Component("Device:R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component("Device:R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    return [r1, r2]


def compare_files(generated_path, reference_path, name):
    """Compare generated file to reference, ignoring UUIDs."""
    print(f"\n🔍 Comparing {name}...")
    
    if not generated_path.exists():
        print(f"❌ Generated file missing: {generated_path}")
        return False
    
    if not reference_path.exists():
        print(f"❌ Reference file missing: {reference_path}")
        return False
    
    # Read files
    with open(generated_path, 'r') as f:
        generated = f.read()
    with open(reference_path, 'r') as f:
        reference = f.read()
    
    print(f"📊 Generated: {len(generated)} chars, Reference: {len(reference)} chars")
    
    # Check basic structure
    gen_symbols = generated.count("(symbol")
    ref_symbols = reference.count("(symbol")
    print(f"   Symbols: Generated={gen_symbols}, Reference={ref_symbols}")
    
    # Show first few differences
    gen_lines = generated.split('\n')
    ref_lines = reference.split('\n')
    
    diff = list(difflib.unified_diff(ref_lines, gen_lines, 
                                   fromfile=f"reference/{name}", 
                                   tofile=f"generated/{name}",
                                   n=2))
    
    if len(diff) > 0:
        print(f"   First 10 differences:")
        for line in diff[:10]:
            if line.startswith(('+++', '---', '@@')):
                continue
            print(f"     {line[:80]}")
    
    return gen_symbols == ref_symbols


def main():
    print("🧪 Simple Circuit Generation Test")
    
    # Generate the 3 circuits
    circuits = [
        (blank_schematic, "blank"),
        (single_resistor, "single"),  
        (two_resistors, "two")
    ]
    
    for circuit_func, name in circuits:
        print(f"\n📋 Generating {name}_schematic...")
        
        try:
            circuit = circuit_func()
            circuit.generate_kicad_project(project_name=f"{name}_generated")
            print(f"✅ Generated {name}_generated/")
        except Exception as e:
            print(f"❌ Failed to generate {name}: {e}")
            continue
        
        # Compare to reference
        generated_sch = Path(f"{name}_generated") / f"{name}_generated.kicad_sch"
        reference_sch = Path(f"{name}_schematic") / f"{name}_schematic.kicad_sch"
        
        if name == "single":
            reference_sch = Path("single_resistor") / "single_resistor.kicad_sch"
        elif name == "two":
            reference_sch = Path("two_resistors") / "two_resistors.kicad_sch"
        
        match = compare_files(generated_sch, reference_sch, f"{name}_schematic")
        
        if match:
            print(f"✅ {name}_schematic structure matches!")
        else:
            print(f"❌ {name}_schematic structure differs")


if __name__ == "__main__":
    main()