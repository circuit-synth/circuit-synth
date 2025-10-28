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

    # Main circuit components

    # Instantiate top-level subcircuits
    child1_circuit = child1(gnd, vin)

    # Main circuit connections
    r3[2] += gnd
    r3[1] += vin

    # Connections
    r2[2] += gnd
    r2[1] += vin

    # Connections
    r2[2] += gnd
    r2[1] += vin

    # Connections
    r2[2] += gnd
    r2[1] += vin

    # Connections
    r2[2] += gnd
    r2[1] += vin

    # Connections
    r2[2] += gnd
    r2[1] += vin

    # Connections
    r2[2] += gnd
    r2[1] += vin

    # Connections
    r2[2] += gnd
    r2[1] += vin

    # Connections
    r2[2] += gnd
    r2[1] += vin

    # Connections
    r2[2] += gnd
    r2[1] += vin

    # Connections
    r2[2] += gnd
    r2[1] += vin
    # Create nets
    gnd = Net("GND")
    vin = Net("VIN")

    # Create components
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Connections
    r2[2] += gnd
    r2[1] += vin


# Generate the circuit
if __name__ == "__main__":
    circuit = main()
    # Generate KiCad project (creates directory)
    circuit.generate_kicad_project(project_name="03_dual_hierarchy_connected_generated")
    # Generate KiCad netlist (required for ratsnest display)
    circuit.generate_kicad_netlist(
        "03_dual_hierarchy_connected_generated/03_dual_hierarchy_connected_generated.net"
    )
