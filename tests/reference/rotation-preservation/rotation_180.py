#!/usr/bin/env python3
"""Reference circuit for 180° rotation testing."""

from circuit_synth import circuit, Component, Net


@circuit(name="rotation_180")
def rotation_180():
    """Single resistor for 180° rotation test."""

    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    r1[1] += vcc
    r1[2] += gnd


if __name__ == "__main__":
    circuit_obj = rotation_180()
    circuit_obj.generate_kicad_project(
        project_name="rotation_180",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    print("✅ rotation_180 generated!")
