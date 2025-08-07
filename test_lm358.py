#!/usr/bin/env python3
"""
Minimal test script for LM358 multi-unit component.
"""

import rust_kicad_schematic_writer as kicad

print("=== TESTING LM358 MULTI-UNIT COMPONENT ===")

# Create minimal schematic
schematic = kicad.create_minimal_schematic()

# Add LM358 (dual op-amp, multi-unit component)
schematic = kicad.add_component_to_schematic(
    schematic,
    reference="U7",
    lib_id="Amplifier_Operational:LM358",
    value="LM358",
    x=100.0,
    y=100.0,
    rotation=0.0,
    footprint="Package_DIP:DIP-8_W7.62mm"
)

print("✓ Added U7: LM358")

# Write to file
output_path = "test_lm358.kicad_sch"
with open(output_path, 'w') as f:
    f.write(schematic)

print(f"✓ Generated {output_path}")

# Check the output
with open(output_path, 'r') as f:
    content = f.read()
    
    # Look for unit names
    import re
    unit_names = re.findall(r'symbol "([^"]*LM[^"]*)"', content)
    print("\nFound symbol/unit names:")
    for name in unit_names:
        print(f"  - {name}")
    
    # Check for problematic patterns
    if "LM2904" in content:
        print("\n⚠️  WARNING: Found LM2904 (parent symbol) instead of LM358!")
    
    if "_2_1" in content:
        print("\n⚠️  WARNING: Found '_2_1' unit naming pattern (should be '_1_1', '_2_1', '_3_1' for units)")

print("\n" + "="*50)
print("Compare this with kicad_reference.kicad_sch to see the difference")