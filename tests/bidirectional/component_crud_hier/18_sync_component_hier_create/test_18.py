#!/usr/bin/env python3
"""
Circuit for Test 18: Add Component in Subcircuit

Add component to hierarchical sheet

Test operation: Add R3 in subcircuit
"""

from circuit_synth import circuit, Component, Net


@circuit(name="test_18")
def test_18():
    """Test circuit for Add Component in Subcircuit."""

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
    circuit_obj = test_18()
    circuit_obj.generate_kicad_project(
        project_name="test_18",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    print("✅ Test 18 circuit generated!")
