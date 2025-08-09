#!/usr/bin/env python3
"""
Main circuit generated from KiCad
"""

from circuit_synth import *

# Import subcircuit functions
from child1 import child1

@circuit(name='main')
def main():
    """
    Main circuit with hierarchical subcircuits
    """
    # Main circuit nets
    gnd = Net('GND')
    unconnectedn_r1npad1_ = Net('unconnected-(R1-Pad1)')

    # Main circuit components
    r1 = Component(symbol="Device:R", ref="R1", value="R")

    # Instantiate top-level subcircuits
    child1_circuit = child1(gnd)

    # Main circuit connections
    r1[2] += gnd

# Generate the circuit
if __name__ == '__main__':
    circuit = main()
    # Generate KiCad project (creates directory)
    circuit.generate_kicad_project(project_name="reference_generated")
    # Generate KiCad netlist (required for ratsnest display)
    circuit.generate_kicad_netlist("reference_generated/reference_generated.net")