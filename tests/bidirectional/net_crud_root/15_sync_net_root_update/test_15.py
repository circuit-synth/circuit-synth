#!/usr/bin/env python3
"""
Circuit for Test 15: Update Net Connection

Modify which pins a net connects to

Test operation: Change R2[2] from CLK to DATA
"""

from circuit_synth import circuit, Component, Net


@circuit(name="test_15")
def test_15():
    """Test circuit for Update Net Connection."""

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
    circuit_obj = test_15()
    circuit_obj.generate_kicad_project(
        project_name="test_15",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    print("✅ Test 15 circuit generated!")
