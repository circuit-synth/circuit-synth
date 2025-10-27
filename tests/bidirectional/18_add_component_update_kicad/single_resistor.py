#!/usr/bin/env python3
"""
Fixture: Single resistor circuit.

Starting point for testing adding a component and updating KiCad.
Run once to generate initial KiCad, then modify this file to add R2.
"""

from circuit_synth import circuit, Component


@circuit(name="single_resistor")
def single_resistor():
    """Circuit with single resistor."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )


if __name__ == "__main__":
    circuit_obj = single_resistor()
    circuit_obj.generate_kicad_project(project_name="single_resistor")
    print("✅ Single resistor circuit generated!")
    print("📁 Open in KiCad: single_resistor/single_resistor.kicad_pro")
    print("")
    print("⚠️  NEXT STEP: Manually edit this file to add R2, then run again")
