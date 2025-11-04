#!/usr/bin/env python3
"""
Reference circuit for rotation preservation testing.

Simple circuit with 3 components that will be rotated manually in KiCad.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="rotation_reference")
def rotation_reference():
    """Simple circuit with R1, R2, C1 for rotation testing."""

    # Components
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Power
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # Signal net
    data = Net("DATA")

    # Connections
    r1[1] += data
    c1[1] += data
    r1[2] += vcc
    r2[1] += vcc
    r2[2] += gnd
    c1[2] += gnd


if __name__ == "__main__":
    circuit_obj = rotation_reference()
    circuit_obj.generate_kicad_project(
        project_name="rotation_reference",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    print("✅ Reference circuit generated!")
    print("📁 Open: tests/reference/rotation-preservation/rotation_reference/rotation_reference.kicad_sch")
