#!/usr/bin/env python3
"""
Circuit for Test 21: Delete Component in Subcircuit

Delete component from hierarchical sheet

Test operation: Delete subcircuit R2
"""

from circuit_synth import circuit, Component, Net


@circuit(name="test_21")
def test_21():
    """Test circuit for Delete Component in Subcircuit."""

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
    circuit_obj = test_21()
    circuit_obj.generate_kicad_project(
        project_name="test_21",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    print("✅ Test 21 circuit generated!")
