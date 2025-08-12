#!/usr/bin/env python3
"""
Manual Test 3: Add a second resistor to existing schematic
"""

import sys
from pathlib import Path
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from circuit_synth.kicad.atomic_operations_exact import add_component_to_schematic_exact

def main():
    print("Manual Test 3: Add Second Resistor")
    print("=" * 35)
    
    # We'll use the result from manual_test_2
    source_path = Path("manual_atomic/manual_atomic.kicad_sch")
    target_path = Path("manual_two_resistors/manual_two_resistors.kicad_sch")
    
    if not source_path.exists():
        print("❌ Source schematic not found. Run manual_test_2_add_resistor.py first!")
        return
    
    # Copy the single resistor schematic
    target_path.parent.mkdir(exist_ok=True)
    shutil.copy2(source_path, target_path)
    
    print(f"📋 Copied schematic from {source_path} to {target_path}")
    
    # Check initial state
    with open(target_path, 'r') as f:
        initial_content = f.read()
    
    print(f"📊 Initial size: {len(initial_content)} chars")
    print(f"📊 Initial symbols: {initial_content.count('(symbol')}")
    
    # Add second resistor
    print("\n⚡ Adding R2 using exact atomic operations...")
    success = add_component_to_schematic_exact(
        target_path,
        lib_id="Device:R",
        reference="R2", 
        value="22k",
        position=(137.16, 68.58),
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    print(f"🔍 Add R2 result: {success}")
    
    # Check final result
    if target_path.exists():
        with open(target_path, 'r') as f:
            final_content = f.read()
        
        print(f"✅ Final schematic updated")
        print(f"📊 Final size: {len(final_content)} chars") 
        print(f"📊 Final symbols: {final_content.count('(symbol')}")
        
        # Check content
        has_r1 = "R1" in final_content
        has_r2 = "R2" in final_content
        has_10k = "10k" in final_content
        has_22k = "22k" in final_content
        
        print(f"📊 Contains R1: {has_r1}")
        print(f"📊 Contains R2: {has_r2}")
        print(f"📊 Contains 10k: {has_10k}")
        print(f"📊 Contains 22k: {has_22k}")
        
        print("\n📄 Final schematic content:")
        print(final_content)
    else:
        print("❌ Target schematic missing after operation")

if __name__ == "__main__":
    main()