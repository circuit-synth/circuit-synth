#!/usr/bin/env python3
"""Test circuit for Metadata Round-Trip."""
from circuit_synth import circuit, Component, Net

@circuit(name="metadata_circuit")
def metadata_circuit():
    """Test circuit with custom properties, annotations."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    vcc, gnd = Net(name="VCC"), Net(name="GND")
    r1[1] += vcc; r1[2] += gnd

if __name__ == "__main__":
    circuit_obj = metadata_circuit()
    circuit_obj.generate_kicad_project(project_name="metadata_circuit", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ Test 06 circuit generated")
