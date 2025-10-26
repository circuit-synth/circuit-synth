#!/usr/bin/env python3
"""Nets & connectivity test reference circuit."""
from circuit_synth import circuit, Component, Net

@circuit(name="netted_circuit")
def netted_circuit():
    """Circuit with nets and connections."""
    vcc = Net("VCC")
    gnd = Net("GND")
    r1 = Component(symbol="Device:R", ref="R1", value="10k")

if __name__ == "__main__":
    netted_circuit().generate_kicad_project(project_name="netted_circuit", placement_algorithm="simple")
