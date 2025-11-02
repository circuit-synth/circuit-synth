#!/usr/bin/env python3
"""Regression test for issue #238 - Text class parameters."""
from circuit_synth import circuit, Component, Net

@circuit(name="text_test")
def text_test():
    """Simple circuit to test text/label handling."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    vcc = Net(name="VCC")
    gnd = Net(name="GND")
    r1[1] += vcc
    r1[2] += gnd

if __name__ == "__main__":
    circuit_obj = text_test()
    circuit_obj.generate_kicad_project(project_name="text_test", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ Text parameters regression test passed")
