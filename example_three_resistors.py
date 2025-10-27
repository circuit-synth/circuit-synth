#!/usr/bin/env python3
"""
Simple example: Three resistors in series using kicad-pcb-api

This example demonstrates the migration to kicad-pcb-api.
Run this to see the new integration in action!

Usage:
    python example_three_resistors.py

Output:
    - three_resistors.kicad_sch (schematic)
    - three_resistors.kicad_pcb (PCB with hierarchical placement)
"""

from pathlib import Path
from circuit_synth import Circuit, Component, Net, circuit

# Create output directory
output_dir = Path("example_output")
output_dir.mkdir(exist_ok=True)

print("🔧 Creating circuit with 3 resistors...")

@circuit
def three_resistors():
    """Three resistors in series: VCC -> R1 -> R2 -> R3 -> GND"""
    # Add three resistors in series with footprints
    r1 = Component("Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component("Device:R", ref="R2", value="22k", footprint="Resistor_SMD:R_0603_1608Metric")
    r3 = Component("Device:R", ref="R3", value="47k", footprint="Resistor_SMD:R_0603_1608Metric")

    # Create nets
    vcc = Net("VCC")
    gnd = Net("GND")

    # Connect resistors in series
    # VCC -> R1 -> R2 -> R3 -> GND
    r1["1"] += vcc
    r1["2"] += r2["1"]
    r2["2"] += r3["1"]
    r3["2"] += gnd

# Create the circuit instance
circ = three_resistors()

print(f"  ✅ Added {len(circ.components)} components")
print(f"  ✅ Created {len(circ.nets)} nets")

# Generate KiCad project (schematic and PCB)
print("\n📐 Generating KiCad project...")
result = circ.generate_kicad_project(
    project_name=str(output_dir / "three_resistors"),
    generate_pcb=True,
    force_regenerate=True,
    placement_algorithm="hierarchical"  # kicad-pcb-api supports 'hierarchical' or 'spiral'
)
print(f"  ✅ Project: {result.get('project_path', 'N/A')}")

# Show PCB statistics using kicad-pcb-api features
print("\n📊 PCB Statistics (from kicad-pcb-api):")
from kicad_pcb_api import PCBBoard

pcb_file = output_dir / "three_resistors" / "three_resistors.kicad_pcb"
pcb = PCBBoard(str(pcb_file))

print(f"  • Footprints: {len(list(pcb.footprints))}")
for fp in pcb.footprints:
    print(f"    - {fp.reference}: {fp.library}:{fp.name} at ({fp.position.x:.1f}, {fp.position.y:.1f})")

print(f"  • Nets: {len(pcb.pcb_data['nets'])}")
for net in pcb.pcb_data['nets'][:5]:  # Show first 5
    print(f"    - Net {net.number}: {net.name}")

print("\n" + "="*60)
print("✅ SUCCESS! Circuit generated using kicad-pcb-api")
print("="*60)
print(f"\nFiles created in: {output_dir.absolute()}/")
print(f"  - three_resistors.kicad_sch")
print(f"  - three_resistors.kicad_pcb")
print(f"  - three_resistors.kicad_pro")
print(f"\n💡 Open in KiCad to view!")
print("\nThis example demonstrates:")
print("  ✅ kicad-pcb-api integration for PCB manipulation")
print("  ✅ Automatic hierarchical placement")
print("  ✅ Simple 3-resistor series circuit")
