#!/usr/bin/env python3
"""Test 51 - Component rotation preservation."""
from circuit_synth import circuit, Component, Net

@circuit(name="comprehensive_root")
def comprehensive_root():
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="4.7k", footprint="Resistor_SMD:R_0603_1608Metric")
    vcc, gnd = Net(name="VCC"), Net(name="GND")
    r1[1] += vcc; r1[2] += gnd; r2[1] += vcc; r2[2] += gnd

if __name__ == "__main__":
    circuit_obj = comprehensive_root()
    circuit_obj.generate_kicad_project(project_name="comprehensive_root", placement_algorithm="hierarchical", generate_pcb=True)
    print("✅ Generated - rotate R1 in KiCad, then regenerate to test preservation")
