#!/usr/bin/env python3
"""Circuit for BOM generation testing."""
from circuit_synth import circuit, Component, Net

@circuit(name="bom_circuit")
def bom_circuit():
    """Simple circuit for BOM validation."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    c1 = Component(symbol="Device:C", ref="C1", value="100nF", footprint="Capacitor_SMD:C_0603_1608Metric")

    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    r1[1] += vcc
    r1[2] += gnd
    r2[1] += vcc
    r2[2] += gnd
    c1[1] += vcc
    c1[2] += gnd

if __name__ == "__main__":
    circuit_obj = bom_circuit()
    circuit_obj.generate_kicad_project(project_name="bom_circuit", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ BOM circuit generated")
