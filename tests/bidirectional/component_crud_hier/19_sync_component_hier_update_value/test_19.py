#!/usr/bin/env python3
"""
Circuit for Test 19: Update Component Value in Subcircuit

Update component value in hierarchical sheet

Test operation: Update subcircuit R1: 10k → 47k
"""

from circuit_synth import circuit, Component, Net


@circuit(name="test_19")
def test_19():
    """Test circuit for Update Component Value in Subcircuit."""

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
    circuit_obj = test_19()
    circuit_obj.generate_kicad_project(
        project_name="test_19",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    print("✅ Test 19 circuit generated!")
