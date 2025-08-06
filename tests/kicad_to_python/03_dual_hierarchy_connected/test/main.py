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
    gnd = Net("GND")
    vin = Net("VIN")

    # Main circuit components
    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Instantiate subcircuits
    child1_instance = child1(gnd, vin)

    # Main circuit connections
    r3[2] += gnd
    r3[1] += vin


# Generate the circuit
if __name__ == "__main__":
    circuit = main()
    # Generate KiCad netlist (required for ratsnest display)
    circuit.generate_kicad_netlist(
        "03_dual_hierarchy_connected_generated/03_dual_hierarchy_connected_generated.net"
    )
    circuit.generate_kicad_project(project_name="03_dual_hierarchy_connected_generated")
