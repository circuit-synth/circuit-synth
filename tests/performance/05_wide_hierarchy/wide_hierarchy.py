#!/usr/bin/env python3
"""Wide hierarchy circuit for performance testing."""
from circuit_synth import circuit, Component, Net

# Create 30 subcircuit functions
def create_subcircuit(idx):
    @circuit(name=f"subcircuit_{idx}")
    def subcircuit(sig_in, sig_out):
        r = Component(symbol="Device:R", ref=f"R{idx}", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
        r[1] += sig_in
        r[2] += sig_out
    return subcircuit

# Generate subcircuits
subcircuits = [create_subcircuit(i) for i in range(1, 31)]

@circuit(name="wide_hierarchy")
def wide_hierarchy():
    """Wide hierarchy with 30 subcircuits."""
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # Instantiate all 30 subcircuits in parallel
    for i, subcircuit_func in enumerate(subcircuits, 1):
        sig = Net(name=f"SIG_{i}")
        subcircuit_func(sig_in=vcc, sig_out=sig)

if __name__ == "__main__":
    import time
    start = time.time()
    circuit_obj = wide_hierarchy()
    circuit_obj.generate_kicad_project(project_name="wide_hierarchy", placement_algorithm="hierarchical", generate_pcb=True)
    elapsed = time.time() - start
    print(f"✅ Wide hierarchy circuit generated in {elapsed:.2f}s")
