#!/usr/bin/env python3
"""
Manual Test 4: Remove a resistor from schematic with two resistors
"""

import sys
from pathlib import Path
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from circuit_synth.kicad.atomic_operations import remove_component_from_schematic

def main():
    print("Manual Test 4: Remove Resistor")
    print("=" * 30)
    
    # Use the result from manual_test_3
    source_path = Path("manual_two_resistors/manual_two_resistors.kicad_sch")
    target_path = Path("manual_remove_test/manual_remove_test.kicad_sch")
    
    if not source_path.exists():
        print("❌ Source schematic not found. Run manual_test_3_add_second_resistor.py first!")
        return
    
    # Copy the two resistor schematic
    target_path.parent.mkdir(exist_ok=True)
    shutil.copy2(source_path, target_path)
    
    print(f"📋 Copied schematic from {source_path} to {target_path}")
    
    # Check initial state
    with open(target_path, 'r') as f:
        initial_content = f.read()
    
    print(f"📊 Initial size: {len(initial_content)} chars")
    print(f"📊 Initial symbols: {initial_content.count('(symbol')}")
    print(f"📊 Initial R1: {'R1' in initial_content}")
    print(f"📊 Initial R2: {'R2' in initial_content}")
    
    # Remove R1
    print("\n🗑️  Removing R1 using atomic operations...")
    success = remove_component_from_schematic(target_path, "R1")
    
    print(f"🔍 Remove R1 result: {success}")
    
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
        
        if not has_r1 and has_r2 and has_22k and not has_10k:
            print("🎉 SUCCESS: R1 removed, R2 remains!")
        else:
            print("⚠️  WARNING: Unexpected component state")
        
        print("\n📄 Final schematic content:")
        print(final_content)
    else:
        print("❌ Target schematic missing after operation")

if __name__ == "__main__":
    main()