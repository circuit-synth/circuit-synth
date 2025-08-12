#!/usr/bin/env python3
"""
Simple test of atomic KiCad operations.

This test demonstrates the simple atomic add/remove operations:
1. Generate a blank schematic
2. Add a single resistor
3. Add a second resistor  
4. Remove the first resistor
5. Verify final state
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from circuit_synth import circuit
from circuit_synth.kicad.atomic_operations import (
    add_component_to_schematic,
    remove_component_from_schematic
)

# Define blank_schematic function
@circuit(name="blank_schematic")
def blank_schematic():
    """A blank schematic circuit."""
    pass


def main():
    print("🧪 Testing simple atomic KiCad operations...")
    
    # Step 1: Generate blank schematic
    print("\n📝 Step 1: Generating blank schematic")
    circuit = blank_schematic()
    circuit.generate_kicad_project(project_name="atomic_test")
    
    schematic_path = Path("atomic_test") / "atomic_test.kicad_sch"
    
    if not schematic_path.exists():
        print("❌ Failed to generate blank schematic")
        return
    
    print(f"✅ Blank schematic created at: {schematic_path}")
    
    # Step 2: Add first resistor
    print("\n⚡ Step 2: Adding first resistor (R1)")
    success = add_component_to_schematic(
        schematic_path,
        lib_id="Device:R",
        reference="R1",
        value="10k",
        position=(121.92, 68.58),
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    if success:
        print("✅ Added R1 (10k resistor)")
    else:
        print("❌ Failed to add R1")
        return
    
    # Step 3: Add second resistor
    print("\n⚡ Step 3: Adding second resistor (R2)")
    success = add_component_to_schematic(
        schematic_path,
        lib_id="Device:R", 
        reference="R2",
        value="22k",
        position=(121.92, 88.58),
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    if success:
        print("✅ Added R2 (22k resistor)")
    else:
        print("❌ Failed to add R2")
        return
    
    # Step 4: Remove first resistor
    print("\n🗑️  Step 4: Removing first resistor (R1)")
    success = remove_component_from_schematic(schematic_path, "R1")
    
    if success:
        print("✅ Removed R1")
    else:
        print("❌ Failed to remove R1")
        return
    
    # Step 5: Verify final state
    print("\n🔍 Step 5: Verifying final state")
    with open(schematic_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    has_r1 = "R1" in content
    has_r2 = "R2" in content
    has_22k = "22k" in content
    has_10k = "10k" in content
    
    print(f"   R1 present: {has_r1}")
    print(f"   R2 present: {has_r2}")
    print(f"   10k value present: {has_10k}")
    print(f"   22k value present: {has_22k}")
    
    if not has_r1 and has_r2 and has_22k and not has_10k:
        print("\n🎉 SUCCESS: Atomic operations work correctly!")
        print("   - R1 was successfully removed")
        print("   - R2 remains with 22k value")
        print("   - No 10k value remains")
    else:
        print("\n❌ FAILURE: Expected R2 only, but state is incorrect")
    
    print(f"\n📁 Generated files in: {Path('atomic_test').absolute()}")


if __name__ == "__main__":
    main()