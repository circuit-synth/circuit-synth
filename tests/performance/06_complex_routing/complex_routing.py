#!/usr/bin/env python3
"""Complex routing circuit for performance testing."""
from circuit_synth import circuit, Component, Net

@circuit(name="complex_routing")
def complex_routing():
    """Circuit with high net density (50 components, 50 nets)."""
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # Create 50 resistors with interconnections
    components = []
    nets = []

    for i in range(1, 51):
        r = Component(symbol="Device:R", ref=f"R{i}", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
        components.append(r)
        net = Net(name=f"NET_{i}")
        nets.append(net)

    # Connect in chain with high density
    for i in range(len(components)):
        if i == 0:
            components[i][1] += vcc
            components[i][2] += nets[i]
        elif i == len(components) - 1:
            components[i][1] += nets[i-1]
            components[i][2] += gnd
        else:
            components[i][1] += nets[i-1]
            components[i][2] += nets[i]

if __name__ == "__main__":
    import time
    start = time.time()
    circuit_obj = complex_routing()
    circuit_obj.generate_kicad_project(project_name="complex_routing", placement_algorithm="hierarchical", generate_pcb=True)
    elapsed = time.time() - start
    print(f"✅ Complex routing circuit generated in {elapsed:.2f}s")
