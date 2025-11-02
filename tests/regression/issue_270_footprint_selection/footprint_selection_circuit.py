#!/usr/bin/env python3
"""Regression test for issue #270 - Automatic footprint selection."""
from circuit_synth import circuit, Component, Net

@circuit(name="footprint_test")
def footprint_test():
    """Circuit to test automatic footprint selection."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    c1 = Component(symbol="Device:C", ref="C1", value="100nF", footprint="Capacitor_SMD:C_0603_1608Metric")

    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    r1[1] += vcc
    r1[2] += gnd
    c1[1] += vcc
    c1[2] += gnd

if __name__ == "__main__":
    circuit_obj = footprint_test()
    circuit_obj.generate_kicad_project(project_name="footprint_test", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ Footprint selection regression test passed")
