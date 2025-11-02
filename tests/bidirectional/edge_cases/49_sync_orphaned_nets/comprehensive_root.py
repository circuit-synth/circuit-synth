#!/usr/bin/env python3
"""Test 49 - Orphaned nets (nets with no connections)."""

from circuit_synth import circuit, Component, Net


@circuit(name="comprehensive_root")
def comprehensive_root():
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")

    vcc = Net(name="VCC")
    gnd = Net(name="GND")
    orphaned = Net("ORPHANED")  # No connections!

    r1[1] += vcc
    r1[2] += gnd


if __name__ == "__main__":
    circuit_obj = comprehensive_root()
    circuit_obj.generate_kicad_project(project_name="comprehensive_root", placement_algorithm="hierarchical", generate_pcb=True)
    print("✅ Circuit with orphaned net generated")
