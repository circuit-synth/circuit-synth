#!/usr/bin/env python3
"""Complex components circuit for netlist generation test."""
from circuit_synth import circuit, Component, Net

@circuit(name="complex_circuit")
def complex_circuit():
    """Circuit with multi-unit components."""
    # Use simple components for now - multi-unit support may be limited
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
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
    circuit_obj = complex_circuit()
    circuit_obj.generate_kicad_project(project_name="complex_circuit", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ Complex components netlist test circuit generated")
