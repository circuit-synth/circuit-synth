#!/usr/bin/env python3
from circuit_synth import *


@circuit(name="BlankCircuit")
def blank():
    """look at the commments"""
    pass


if __name__ == "__main__":
    circuit_obj = blank()
    circuit_obj.generate_kicad_project(
        project_name="BlankTest", placement_algorithm="hierarchical", generate_pcb=True
    )
    print("Generated BlankTest/")
