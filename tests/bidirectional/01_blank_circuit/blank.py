#!/usr/bin/env python3
from circuit_synth import circuit


@circuit(name="blank")
def blank():
    """Blank circuit"""
    pass


if __name__ == "__main__":
    circuit_obj = blank()
    circuit_obj.generate_kicad_project(project_name="blank")
