#!/usr/bin/env python3
"""Hierarchical circuit for netlist generation test."""
from circuit_synth import circuit, Component, Net

@circuit(name="amplifier")
def amplifier_stage(input_sig, output_sig, vcc, gnd):
    """Simple amplifier subcircuit."""
    r1 = Component(symbol="Device:R", ref="R1", value="100k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r3 = Component(symbol="Device:R", ref="R3", value="1k", footprint="Resistor_SMD:R_0603_1608Metric")
    r1[1] += input_sig
    r1[2] += output_sig
    r2[1] += output_sig
    r2[2] += gnd
    r3[1] += vcc
    r3[2] += output_sig

@circuit(name="hierarchical_circuit")
def hierarchical_circuit():
    """Circuit with subcircuits for netlist validation."""
    vcc = Net(name="VCC")
    gnd = Net(name="GND")
    sig_in = Net(name="SIG_IN")
    sig_out = Net(name="SIG_OUT")

    # Instantiate amplifier subcircuit
    amplifier_stage(input_sig=sig_in, output_sig=sig_out, vcc=vcc, gnd=gnd)

if __name__ == "__main__":
    circuit_obj = hierarchical_circuit()
    circuit_obj.generate_kicad_project(project_name="hierarchical_circuit", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ Hierarchical netlist test circuit generated")
