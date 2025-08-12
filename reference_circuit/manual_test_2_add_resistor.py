#!/usr/bin/env python3
"""
Manual Test 2: Add a single resistor to blank schematic using atomic operations
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from circuit_synth import *
from circuit_synth.kicad.atomic_operations_exact import add_component_to_schematic_exact

@circuit(name="blank_for_atomic")
def blank_for_atomic():
    """A blank schematic circuit."""
    pass

def main():
    print("Manual Test 2: Add Resistor with Atomic Operations")
    print("=" * 50)
    
    # Step 1: Create truly blank schematic directly
    print("\n🔧 Step 1: Creating blank schematic...")
    schematic_path = Path("manual_atomic/manual_atomic.kicad_sch")
    schematic_path.parent.mkdir(exist_ok=True)
    
    # Create minimal blank schematic matching reference format
    blank_content = '''(kicad_sch
	(version 20250114)
	(generator "eeschema")
	(generator_version "9.0")
	(uuid "c607e5f1-42e2-4249-b659-6d0555bce224")
	(paper "A4")
	(lib_symbols
	)
	(sheet_instances
		(path "/"
			(page "1")
		)
	)
	(embedded_fonts no)
)'''
    
    with open(schematic_path, 'w') as f:
        f.write(blank_content)
    
    # Check blank schematic
    if schematic_path.exists():
        with open(schematic_path, 'r') as f:
            blank_content = f.read()
        print(f"✅ Blank schematic created")
        print(f"📊 Blank size: {len(blank_content)} chars")
        print(f"📊 Blank symbols: {blank_content.count('(symbol')}")
    else:
        print("❌ Failed to create blank schematic")
        return
    
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
        
        # Check for R1 content
        has_r1 = "R1" in final_content
        has_10k = "10k" in final_content
        has_device_r = "Device:R" in final_content
        
        print(f"📊 Contains R1: {has_r1}")
        print(f"📊 Contains 10k: {has_10k}")
        print(f"📊 Contains Device:R: {has_device_r}")
        
        print("\n📄 Final schematic content:")
        print(final_content)
    else:
        print("❌ Schematic file missing after atomic operation")

if __name__ == "__main__":
    main()