#!/usr/bin/env python3
"""
Simple test with just a few components including multi-unit ones.
"""

import rust_kicad_schematic_writer as kicad

print("=== SIMPLE MULTI-COMPONENT TEST ===")

# Create minimal schematic
schematic = kicad.create_minimal_schematic()

# Add components one by one
components = [
    ("U1", "MCU_ST_STM32F1:STM32F103C8Tx", "STM32F103C8T6", 50, 50),  # Extended, single unit
    ("U2", "Amplifier_Operational:LM358", "LM358", 100, 50),          # Extended, multi-unit
    ("U3", "Regulator_Linear:AMS1117-3.3", "AMS1117-3.3", 150, 50),  # Extended, single unit
]

for ref, lib_id, value, x, y in components:
    print(f"Adding {ref}: {value}...", end=" ")
    try:
        schematic = kicad.add_component_to_schematic(
            schematic,
            reference=ref,
            lib_id=lib_id,
            value=value,
            x=float(x),
            y=float(y),
            rotation=0.0,
            footprint=""
        )
        print("✓")
    except Exception as e:
        print(f"✗ {e}")

# Write to file
output_path = "test_simple_multi.kicad_sch"
with open(output_path, 'w') as f:
    f.write(schematic)

print(f"\nGenerated {output_path}")

# Validate with KiCad
import subprocess
result = subprocess.run(
    ["kicad-cli", "sch", "export", "pdf", output_path, "--output", "test_simple_multi.pdf"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ KiCad validation PASSED!")
else:
    print(f"❌ KiCad validation FAILED: {result.stderr}")