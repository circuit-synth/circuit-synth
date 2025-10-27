#!/usr/bin/env python3
"""
Fixture: Single resistor (no nets).

Starting point for testing adding a new component and new net simultaneously.
"""

from circuit_synth import circuit, Component


@circuit(name="single_resistor")
def single_resistor():
    """Circuit with single resistor, no connections."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )


if __name__ == "__main__":
    circuit_obj = single_resistor()
    circuit_obj.generate_kicad_project(project_name="single_resistor")
    print("✅ Single resistor (no nets) generated!")
    print("📁 Open in KiCad: single_resistor/single_resistor.kicad_pro")
