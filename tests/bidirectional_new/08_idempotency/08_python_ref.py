#!/usr/bin/env python3
"""Idempotency validation reference circuit."""
from circuit_synth import circuit, Component

@circuit(name="idempotent_circuit")
def idempotent_circuit():
    """Circuit for idempotency validation."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k")

if __name__ == "__main__":
    idempotent_circuit().generate_kicad_project(project_name="idempotent_circuit", placement_algorithm="simple")
