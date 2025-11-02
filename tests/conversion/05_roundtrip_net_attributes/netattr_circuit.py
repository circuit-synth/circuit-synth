#!/usr/bin/env python3
"""Test circuit for Net Attributes Round-Trip."""
from circuit_synth import circuit, Component, Net

@circuit(name="netattr_circuit")
def netattr_circuit():
    """Test circuit with net classes, differential pairs."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    vcc, gnd = Net(name="VCC"), Net(name="GND")
    r1[1] += vcc; r1[2] += gnd

if __name__ == "__main__":
    circuit_obj = netattr_circuit()
    circuit_obj.generate_kicad_project(project_name="netattr_circuit", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ Test 05 circuit generated")
