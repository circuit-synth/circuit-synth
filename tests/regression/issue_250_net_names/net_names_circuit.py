#!/usr/bin/env python3
"""Regression test for issue #250 - Net name preservation."""
from circuit_synth import circuit, Component, Net

@circuit(name="netname_test")
def netname_test():
    """Circuit to test net name preservation."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")

    # Use specific net names that should be preserved
    vcc = Net(name="VCC")
    custom_net = Net(name="CUSTOM_SIGNAL")

    r1[1] += vcc
    r1[2] += custom_net

if __name__ == "__main__":
    circuit_obj = netname_test()
    circuit_obj.generate_kicad_project(project_name="netname_test", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ Net name regression test passed")
