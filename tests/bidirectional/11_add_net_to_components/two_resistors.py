#!/usr/bin/env python3
"""
Fixture: Two unconnected resistors.

Starting point for testing adding a net connection to existing components.
"""

from circuit_synth import circuit, Component


@circuit(name="two_resistors")
def two_resistors():
    """Circuit with two resistors - NO connection between them."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    # Note: No Net() defined - components are unconnected
    net1 = Net(ref="N1")
    r1[1] += net1
    r2[1] += net1


if __name__ == "__main__":
    circuit_obj = two_resistors()
    circuit_obj.generate_kicad_project(
        project_name="two_resistors", placement_algorithm="simple", generate_pcb=True
    )
    print("✅ Two unconnected resistors generated!")
    print("📁 Open in KiCad: two_resistors/two_resistors.kicad_pro")
