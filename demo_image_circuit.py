#!/usr/bin/env python3
"""
Demo circuit showcasing image support in circuit-synth.
"""

import sys
from pathlib import Path

# Add kicad-sch-api submodule to path
sys.path.insert(0, str(Path(__file__).parent / "submodules" / "kicad-sch-api"))

from circuit_synth import Circuit, add_image
from circuit_synth.core.component import Component

# Create a demo circuit
circuit = Circuit(name="Image Demo Circuit")

# Add some components
r1 = Component(symbol="Device:R", ref="R1", value="10k")
r2 = Component(symbol="Device:R", ref="R2", value="1k")
c1 = Component(symbol="Device:C", ref="C1", value="100nF")

circuit.add_component(r1)
circuit.add_component(r2)
circuit.add_component(c1)

# Add image - using extracted working screenshot
image_path = str(Path(__file__).parent / "working_screenshot.png")
print(f"Adding image: {image_path}")

# Add the image to the schematic
# Position it in a visible area with appropriate scale
add_image(
    image_path,
    position=(200, 80),  # Position in mm
    scale=0.5  # Scale to 50% of original size
)

print(f"Image added at position (200, 80) with scale 0.5")

# Generate KiCad project
output_dir = "demo_with_image"
circuit.generate_kicad_project(output_dir)

print(f"\n✓ Project generated in: {output_dir}")
print(f"  Schematic: {output_dir}/{output_dir}.kicad_sch")
print(f"\nOpening in KiCad...")
