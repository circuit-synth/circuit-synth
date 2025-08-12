#!/usr/bin/env python3
"""
Test exact atomic operations that match reference formatting
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from circuit_synth import *
from circuit_synth.kicad.atomic_operations_exact import add_component_to_schematic_exact

@circuit(name="blank_exact")
def blank_exact():
    """A blank schematic circuit."""
    pass

def main():
    print("Manual Test: Exact Atomic Operations")
    print("=" * 40)
    
    # Step 1: Generate blank schematic
    print("\n🔧 Step 1: Creating blank schematic...")
    circuit = blank_exact()
    circuit.generate_kicad_project(project_name="manual_exact")
    
    schematic_path = Path("manual_exact/manual_exact.kicad_sch")
    
    # Step 2: Add resistor using exact atomic operations
    print("\n⚡ Step 2: Adding R1 using exact atomic operations...")
    success = add_component_to_schematic_exact(
        schematic_path,
        lib_id="Device:R",
        reference="R1",
        value="10k",
        position=(121.92, 68.58),
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    print(f"🔍 Add operation result: {success}")
    
    # Check result
    if schematic_path.exists():
        with open(schematic_path, 'r') as f:
            final_content = f.read()
        
        print(f"✅ Final schematic updated")
        print(f"📊 Final size: {len(final_content)} chars")
        print(f"📊 Final symbols: {final_content.count('(symbol')}")
        
        # Check for lib definition
        has_lib_def = '"Device:R"' in final_content and 'pin_numbers' in final_content
        has_r1 = "R1" in final_content
        has_10k = "10k" in final_content
        
        print(f"📊 Has Device:R lib definition: {has_lib_def}")
        print(f"📊 Contains R1: {has_r1}")
        print(f"📊 Contains 10k: {has_10k}")
        
        print("\n📄 Final schematic content (first 500 chars):")
        print(final_content[:500] + "..." if len(final_content) > 500 else final_content)
        
        # Save to file for inspection
        with open("exact_output.kicad_sch", 'w') as f:
            f.write(final_content)
        print(f"\n💾 Saved to exact_output.kicad_sch for inspection")
    else:
        print("❌ Schematic file missing after atomic operation")

if __name__ == "__main__":
    main()