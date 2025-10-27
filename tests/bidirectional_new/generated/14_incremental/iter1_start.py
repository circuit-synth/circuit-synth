#!/usr/bin/env python3
from circuit_synth import circuit, Component

@circuit(name="growing_circuit")
def growing_circuit():
    """Iteration 1: Two resistors."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="20k", footprint="Resistor_SMD:R_0603_1608Metric")

if __name__ == "__main__":
    circuit_obj = growing_circuit()
    circuit_obj.generate_kicad_project(project_name="growing_circuit", placement_algorithm="simple", generate_pcb=True)
