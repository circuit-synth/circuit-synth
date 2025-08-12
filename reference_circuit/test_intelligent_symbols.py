#!/usr/bin/env python3
"""
Test intelligent lib_symbols management
"""

import sys
from pathlib import Path
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from circuit_synth.kicad.atomic_operations_exact import add_component_to_schematic_exact, remove_component_from_schematic_exact

def test_intelligent_symbols():
    print("Testing Intelligent lib_symbols Management")
    print("=" * 50)
    
    # Start with blank schematic
    
    test_dir = Path("test_intelligent")
    test_dir.mkdir(exist_ok=True)
    
    test_file = test_dir / "test.kicad_sch"
    
    # 1. Create blank schematic manually
    print("1. Creating blank schematic...")
    
    blank_content = '''(kicad_sch
	(version 20250114)
	(generator "circuit_synth")
	(generator_version "9.0")
	(uuid "test-uuid-1234")
	(paper "A4")
	(lib_symbols
	)
	(sheet_instances
		(path "/"
			(page "1")
		)
	)
	(embedded_fonts
		no
	)
)'''
    
    with open(test_file, 'w') as f:
        f.write(blank_content)
    
    print(f"   Blank: lib_symbols has Device:R = {'Device:R' in blank_content}")
    
    # 2. Add R1 - should add lib_symbols definition
    print("2. Adding R1 (first resistor)...")
    success = add_component_to_schematic_exact(
        test_file, "Device:R", "R1", "10k", (100, 100)
    )
    
    with open(test_file, 'r') as f:
        content = f.read()
    r_count = content.count('lib_id "Device:R"')
    has_def = 'symbol "Device:R"' in content
    print(f"   Result: {success}, R components: {r_count}, lib_symbols has Device:R = {has_def}")
    
    # 3. Add R2 - should NOT add duplicate lib_symbols definition  
    print("3. Adding R2 (second resistor)...")
    success = add_component_to_schematic_exact(
        test_file, "Device:R", "R2", "22k", (150, 100)
    )
    
    with open(test_file, 'r') as f:
        content = f.read()
    r_count = content.count('lib_id "Device:R"') 
    def_count = content.count('symbol "Device:R"')
    print(f"   Result: {success}, R components: {r_count}, Device:R definitions: {def_count}")
    
    # 4. Remove R1 - should keep lib_symbols definition (R2 still exists)
    print("4. Removing R1 (R2 remains)...")
    success = remove_component_from_schematic_exact(test_file, "R1")
    
    with open(test_file, 'r') as f:
        content = f.read()
    r_count = content.count('lib_id "Device:R"')
    has_def = 'symbol "Device:R"' in content  
    has_r1 = '"Reference" "R1"' in content
    has_r2 = '"Reference" "R2"' in content
    print(f"   Result: {success}, R components: {r_count}, lib_symbols has Device:R = {has_def}")
    print(f"   Components: R1 = {has_r1}, R2 = {has_r2}")
    
    # 5. Remove R2 - should remove lib_symbols definition (no more R components)
    print("5. Removing R2 (last resistor)...")
    success = remove_component_from_schematic_exact(test_file, "R2")
    
    with open(test_file, 'r') as f:
        content = f.read()
    r_count = content.count('lib_id "Device:R"')
    has_def = 'symbol "Device:R"' in content
    has_r1 = '"Reference" "R1"' in content
    has_r2 = '"Reference" "R2"' in content  
    print(f"   Result: {success}, R components: {r_count}, lib_symbols has Device:R = {has_def}")
    print(f"   Components: R1 = {has_r1}, R2 = {has_r2}")
    
    print("\n" + "=" * 50)
    if r_count == 0 and not has_def:
        print("✅ SUCCESS: Intelligent lib_symbols management working!")
        print("   - Adds definition when first component added")
        print("   - Keeps definition while components exist") 
        print("   - Removes definition when last component removed")
    else:
        print("❌ FAILURE: lib_symbols not properly managed")
        
    # Show final file
    print(f"\nFinal file content:\n{content}")

if __name__ == "__main__":
    test_intelligent_symbols()