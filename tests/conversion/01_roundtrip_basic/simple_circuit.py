#!/usr/bin/env python3
"""Simple circuit for round-trip testing."""

from circuit_synth import circuit, Component, Net


@circuit(name="simple_circuit")
def simple_circuit():
    """Basic circuit with 3 components for round-trip validation."""

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

    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    r1[1] += vcc
    r1[2] += gnd

    r2[1] += vcc
    r2[2] += gnd

    c1[1] += vcc
    c1[2] += gnd


if __name__ == "__main__":
    circuit_obj = simple_circuit()
    circuit_obj.generate_kicad_project(
        project_name="simple_circuit",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    print("✅ Simple circuit generated for round-trip test")
