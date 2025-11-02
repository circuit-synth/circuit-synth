#!/usr/bin/env python3
"""Circuit for PCB File Generation testing."""
from circuit_synth import circuit, Component, Net

@circuit(name="pcb_gen")
def pcb_gen():
    """Circuit for PCB validation."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="4.7k", footprint="Resistor_SMD:R_0603_1608Metric")
    c1 = Component(symbol="Device:C", ref="C1", value="100nF", footprint="Capacitor_SMD:C_0603_1608Metric")

    vcc = Net(name="VCC")
    gnd = Net(name="GND")
    sig = Net(name="SIGNAL")

    r1[1] += vcc
    r1[2] += sig
    r2[1] += sig
    r2[2] += gnd
    c1[1] += sig
    c1[2] += gnd

if __name__ == "__main__":
    circuit_obj = pcb_gen()
    circuit_obj.generate_kicad_project(project_name="pcb_gen", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ PCB File Generation circuit generated")
