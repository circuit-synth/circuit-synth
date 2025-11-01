#!/usr/bin/env python3
"""
Circuit for Test 20: Rename Component in Subcircuit

Rename component in hierarchical sheet

Test operation: Rename subcircuit R1 → R100
"""

from circuit_synth import circuit, Component, Net


@circuit(name="test_20")
def test_20():
    """Test circuit for Rename Component in Subcircuit."""

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
    circuit_obj = test_20()
    circuit_obj.generate_kicad_project(
        project_name="test_20",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    print("✅ Test 20 circuit generated!")
