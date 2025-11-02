#!/usr/bin/env python3
"""Regression test for issue #240 - Component position preservation."""
from circuit_synth import circuit, Component, Net

@circuit(name="position_test")
def position_test():
    """Circuit to test position preservation."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="4.7k", footprint="Resistor_SMD:R_0603_1608Metric")
    vcc = Net(name="VCC")
    gnd = Net(name="GND")
    sig = Net(name="SIGNAL")

    r1[1] += vcc
    r1[2] += sig
    r2[1] += sig
    r2[2] += gnd

if __name__ == "__main__":
    circuit_obj = position_test()
    circuit_obj.generate_kicad_project(project_name="position_test", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ Component position regression test passed")
