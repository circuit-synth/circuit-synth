#!/usr/bin/env python3
"""Memory usage monitoring test."""
from circuit_synth import circuit, Component, Net
import tracemalloc

@circuit(name="memory_circuit")
def memory_circuit():
    """Circuit for memory monitoring (100 components)."""
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    for i in range(1, 101):
        r = Component(symbol="Device:R", ref=f"R{i}", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
        r[1] += vcc
        r[2] += gnd

if __name__ == "__main__":
    import time
    tracemalloc.start()
    start = time.time()

    circuit_obj = memory_circuit()
    circuit_obj.generate_kicad_project(project_name="memory_circuit", placement_algorithm="hierarchical", generate_pcb=True)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed = time.time() - start

    print(f"✅ Memory circuit generated in {elapsed:.2f}s")
    print(f"   Current memory: {current / 1024 / 1024:.2f} MB")
    print(f"   Peak memory: {peak / 1024 / 1024:.2f} MB")
