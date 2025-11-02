#!/usr/bin/env python3
"""Simple circuit for basic netlist generation test."""
from circuit_synth import circuit, Component, Net

@circuit(name="basic_circuit")
def basic_circuit():
    """Simple RC circuit for netlist validation."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="4.7k", footprint="Resistor_SMD:R_0603_1608Metric")
    c1 = Component(symbol="Device:C", ref="C1", value="100nF", footprint="Capacitor_SMD:C_0603_1608Metric")

    vcc = Net(name="VCC")
    gnd = Net(name="GND")
    signal = Net(name="SIGNAL")

    # Simple voltage divider with capacitor
    r1[1] += vcc
    r1[2] += signal
    r2[1] += signal
    r2[2] += gnd
    c1[1] += signal
    c1[2] += gnd

if __name__ == "__main__":
    circuit_obj = basic_circuit()
    circuit_obj.generate_kicad_project(project_name="basic_circuit", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ Basic netlist test circuit generated")
