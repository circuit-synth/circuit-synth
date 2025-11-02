#!/usr/bin/env python3
"""Test 50 - Component with missing/invalid footprint."""

from circuit_synth import circuit, Component, Net


@circuit(name="comprehensive_root")
def comprehensive_root():
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="")  # Empty footprint
    r2 = Component(symbol="Device:R", ref="R2", value="4.7k", footprint="InvalidLib:InvalidFootprint")

    vcc, gnd = Net(name="VCC"), Net(name="GND")
    r1[1] += vcc; r1[2] += gnd
    r2[1] += vcc; r2[2] += gnd


if __name__ == "__main__":
    circuit_obj = comprehensive_root()
    circuit_obj.generate_kicad_project(project_name="comprehensive_root", placement_algorithm="hierarchical", generate_pcb=True)
    print("✅ Circuit with missing footprints generated")
