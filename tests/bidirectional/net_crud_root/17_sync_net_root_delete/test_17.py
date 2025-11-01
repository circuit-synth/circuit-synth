#!/usr/bin/env python3
"""
Circuit for Test 17: Delete Net

Remove net while preserving other nets

Test operation: Delete CLK net
"""

from circuit_synth import circuit, Component, Net


@circuit(name="test_17")
def test_17():
    """Test circuit for Delete Net."""

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
    circuit_obj = test_17()
    circuit_obj.generate_kicad_project(
        project_name="test_17",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    print("✅ Test 17 circuit generated!")
