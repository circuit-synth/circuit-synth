#!/usr/bin/env python3
"""Regression test for issue #260 - Power symbol generation."""
from circuit_synth import circuit, Component, Net

@circuit(name="power_test")
def power_test():
    """Circuit to test power symbol generation."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")

    vcc = Net(name="VCC")
    v3v3 = Net(name="3V3")
    gnd = Net(name="GND")

    r1[1] += vcc
    r1[2] += gnd
    r2[1] += v3v3
    r2[2] += gnd

if __name__ == "__main__":
    circuit_obj = power_test()
    circuit_obj.generate_kicad_project(project_name="power_test", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ Power symbol regression test passed")
