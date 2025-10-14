#!/usr/bin/env python3
"""Test circuit to verify text width ratio fix for bounding boxes."""

import sys
from pathlib import Path

# Add submodule to path
sys.path.insert(0, str(Path(__file__).parent / "submodules" / "kicad-sch-api"))

from circuit_synth import Component, Net, circuit


@circuit(name="Placement Test")
def placement_test_circuit():
    """Test circuit with various component sizes to test bounding boxes."""
    # Power nets
    vcc = Net("VCC_3V3")
    gnd = Net("GND")

    # Small components (resistors, capacitors)
    r1 = Component(symbol="Device:R", ref="R1", value="10k")
    r2 = Component(symbol="Device:R", ref="R2", value="4.7k")
    c1 = Component(symbol="Device:C", ref="C1", value="100nF")
    c2 = Component(symbol="Device:C", ref="C2", value="10uF")

    # LED
    led1 = Component(symbol="Device:LED", ref="D1", value="LED")

    # Make connections to create pin labels with various net names
    r1["1"] += vcc
    r1["2"] += gnd
    r2["1"] += vcc
    r2["2"] += gnd
    c1["1"] += vcc
    c1["2"] += gnd
    c2["1"] += vcc
    c2["2"] += gnd
    led1["K"] += gnd
    led1["A"] += vcc

    return circuit()


if __name__ == "__main__":
    # Generate with bounding boxes visible
    print("Generating test circuit with bounding boxes...")
    test_circuit = placement_test_circuit()

    test_circuit.generate_kicad_project(
        "test_placement_issues",
        draw_bounding_boxes=True,
        force_regenerate=True
    )

    print("\n✅ Generated! Open test_placement_issues/test_placement_issues.kicad_sch in KiCad")
    print("\nWith text width ratio = 0.65 (down from 1.0):")
    print("  • Bounding boxes should better contain pin labels")
    print("  • Less excessive spacing between components")
    print("  • Labels should not extend far beyond boxes")
