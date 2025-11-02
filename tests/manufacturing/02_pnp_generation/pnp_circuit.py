#!/usr/bin/env python3
"""Circuit for Pick-and-Place (PnP) Data testing."""
from circuit_synth import circuit, Component, Net

@circuit(name="pnp_circuit")
def pnp_circuit():
    """Circuit for manufacturing validation."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="4.7k", footprint="Resistor_SMD:R_0603_1608Metric")
    c1 = Component(symbol="Device:C", ref="C1", value="100nF", footprint="Capacitor_SMD:C_0603_1608Metric")

    vcc = Net(name="VCC")
    gnd = Net(name="GND")
    sig = Net(name="SIGNAL")

    r1[1] += vcc
    r1[2] += sig
    r2[1] += sig
    r2[2] += gnd
    c1[1] += sig
    c1[2] += gnd

if __name__ == "__main__":
    circuit_obj = pnp_circuit()
    circuit_obj.generate_kicad_project(project_name="pnp_circuit", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ Pick-and-Place (PnP) Data circuit generated")
