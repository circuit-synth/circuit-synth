#!/usr/bin/env python3
"""
Circuit for Test 16: Rename Net

Rename net while preserving connections

Test operation: Rename DATA → SIG
"""

from circuit_synth import circuit, Component, Net


@circuit(name="test_16")
def test_16():
    """Test circuit for Rename Net."""

    # Basic circuit
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
    circuit_obj = test_16()
    circuit_obj.generate_kicad_project(
        project_name="test_16",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    print("✅ Test 16 circuit generated!")
