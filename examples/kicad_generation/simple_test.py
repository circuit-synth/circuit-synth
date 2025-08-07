#!/usr/bin/env python3
"""
Simple test script for KiCad schematic generation.
Creates a basic LED circuit with current limiting resistor.
"""

import rust_kicad_schematic_writer as kicad

print("Creating a simple LED circuit...")

# Start with empty schematic
schematic = kicad.create_minimal_schematic()

# Add a resistor
schematic = kicad.add_component_to_schematic(
    schematic,
    reference="R1",
    lib_id="Device:R",
    value="330",
    x=100.0,
    y=50.0,
    rotation=0.0,
    footprint="Resistor_SMD:R_0603_1608Metric"
)
print("✓ Added resistor R1 (330Ω)")

# Add an LED
schematic = kicad.add_component_to_schematic(
    schematic,
    reference="D1",
    lib_id="Device:LED",
    value="RED",
    x=100.0,
    y=80.0,
    rotation=0.0,
    footprint="LED_SMD:LED_0603_1608Metric"
)
print("✓ Added LED D1")

# Add power label
schematic = kicad.add_hierarchical_label_to_schematic(
    schematic,
    name="VCC",
    shape="input",
    x=100.0,
    y=30.0,
    rotation=90.0
)
print("✓ Added VCC power label")

# Add ground label
schematic = kicad.add_hierarchical_label_to_schematic(
    schematic,
    name="GND",
    shape="passive",
    x=100.0,
    y=100.0,
    rotation=270.0
)
print("✓ Added GND label")

# Save the file
with open("led_circuit.kicad_sch", 'w') as f:
    f.write(schematic)

print("\n✅ Done! Created led_circuit.kicad_sch")
print("Open it in KiCad to see your circuit!")