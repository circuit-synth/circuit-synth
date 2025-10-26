#!/usr/bin/env python3
"""User content preservation reference circuit with comments."""
from circuit_synth import circuit, Component

@circuit(name="commented_circuit")
def commented_circuit():
    """
    Circuit with user documentation and comments.
    
    This circuit demonstrates comment preservation through cycles.
    """
    # Main supply resistor
    r1 = Component(symbol="Device:R", ref="R1", value="10k")

if __name__ == "__main__":
    commented_circuit().generate_kicad_project(project_name="commented_circuit", placement_algorithm="simple")
