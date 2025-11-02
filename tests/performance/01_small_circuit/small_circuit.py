#!/usr/bin/env python3
"""Small circuit for performance testing."""
from circuit_synth import circuit, Component, Net

@circuit(name="small_circuit")
def small_circuit():
    """Small circuit with 20 resistors."""
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # Create 20 resistors
    for i in range(1, 21):
        r = Component(symbol="Device:R", ref=f"R{i}", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
        r[1] += vcc
        r[2] += gnd

if __name__ == "__main__":
    import time
    start = time.time()
    circuit_obj = small_circuit()
    circuit_obj.generate_kicad_project(project_name="small_circuit", placement_algorithm="hierarchical", generate_pcb=True)
    elapsed = time.time() - start
    print(f"✅ Small circuit generated in {elapsed:.2f}s")
