#!/usr/bin/env python3
"""Test the simple API for creating new KiCad schematics."""

import rust_kicad_schematic_writer as kicad

print("=== Testing Minimal Schematic API ===\n")

# Test 1: Create minimal schematic with default A4
print("1. Creating minimal schematic (A4)...")
schematic = kicad.create_minimal_schematic()
print(f"   Length: {len(schematic)} chars")
print(f"   Content: {schematic}\n")

# Test 2: Create with custom paper size
print("2. Creating schematic with A3 paper...")
schematic_a3 = kicad.create_empty_schematic("A3")
print(f"   Length: {len(schematic_a3)} chars")
print(f"   Has A3: {'A3' in schematic_a3}")

# Test 3: Format it nicely
print("\n3. Formatted output:")
import re
formatted = re.sub(r'\)\s*\(', ')\n  (', schematic)
formatted = re.sub(r'^\(', '(\n  ', formatted)
formatted = re.sub(r'\)$', '\n)', formatted)
print(formatted)

# Test 4: Save to file
filename = "test_minimal.kicad_sch"
with open(filename, 'w') as f:
    f.write(schematic)
print(f"\n4. Saved to {filename}")

# Test 5: Verify format
print("\n5. Format validation:")
print(f"   ✅ Starts with (kicad_sch: {schematic.startswith('(kicad_sch')}")
print(f"   ✅ Has version: {'version' in schematic}")
print(f"   ✅ Has generator: {'generator' in schematic}")
print(f"   ✅ Has lib_symbols: {'lib_symbols' in schematic}")
print(f"   ✅ Has symbol_instances: {'symbol_instances' in schematic}")
print(f"   ✅ No dotted pairs: {'. ' not in schematic}")

print("\n✨ API test complete! You can open test_minimal.kicad_sch in KiCad.")