#!/usr/bin/env python3
"""
Fixture: Single resistor with changeable footprint.

Circuit with one 10kΩ resistor, used for testing footprint changes:
- SMD to SMD (0603 → 0805)
- SMD to THT (0805 → through-hole)

Tests that footprint changes preserve position and don't affect symbol.
"""

from circuit_synth import circuit, Component


@circuit(name="resistor_footprints")
def resistor_footprints():
    """Circuit with a single 10kΩ resistor (0603 footprint)."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = resistor_footprints()

    circuit_obj.generate_kicad_project(project_name="resistor_footprints")

    print("✅ Resistor circuit generated successfully!")
    print("📁 Open in KiCad: resistor_footprints/resistor_footprints.kicad_pro")
