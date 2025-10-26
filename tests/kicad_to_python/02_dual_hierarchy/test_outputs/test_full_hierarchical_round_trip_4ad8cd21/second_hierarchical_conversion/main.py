#!/usr/bin/env python3
"""
Main circuit generated from KiCad
"""

# Import subcircuit functions
from child1 import child1

from circuit_synth import *


@circuit(name="main")
def main():
    """
    Main circuit with hierarchical subcircuits
    """
    # Main circuit nets
    unconnectedn_r1npad1_ = Net("unconnected-(R1-Pad1)")
    unconnectedn_r1npad2_ = Net("unconnected-(R1-Pad2)")

    # Main circuit components
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Instantiate top-level subcircuits
    child1_circuit = child1()


# Generate the circuit
if __name__ == "__main__":
    circuit = main()
    # Generate KiCad project (creates directory)
    circuit.generate_kicad_project(project_name="02_dual_hierarchy_generated_generated")
    # Generate KiCad netlist (required for ratsnest display)
    circuit.generate_kicad_netlist(
        "02_dual_hierarchy_generated_generated/02_dual_hierarchy_generated_generated.net"
    )
