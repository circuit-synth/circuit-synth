#!/usr/bin/env python3
"""Round-trip validation reference circuit."""
from circuit_synth import circuit, Component

@circuit(name="roundtrip_circuit")
def roundtrip_circuit():
    """Simple circuit for round-trip validation."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k")

if __name__ == "__main__":
    roundtrip_circuit().generate_kicad_project(project_name="roundtrip_circuit", placement_algorithm="simple")
