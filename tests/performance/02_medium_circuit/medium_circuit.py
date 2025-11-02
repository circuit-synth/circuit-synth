#!/usr/bin/env python3
"""Medium circuit for performance testing."""
from circuit_synth import circuit, Component, Net

@circuit(name="medium_circuit")
def medium_circuit():
    """Medium circuit with 200 components."""
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # Create 200 resistors
    for i in range(1, 201):
        r = Component(symbol="Device:R", ref=f"R{i}", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
        r[1] += vcc
        r[2] += gnd

if __name__ == "__main__":
    import time
    start = time.time()
    circuit_obj = medium_circuit()
    circuit_obj.generate_kicad_project(project_name="medium_circuit", placement_algorithm="hierarchical", generate_pcb=True)
    elapsed = time.time() - start
    print(f"✅ Medium circuit generated in {elapsed:.2f}s")
