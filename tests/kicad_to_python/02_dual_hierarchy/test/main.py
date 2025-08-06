#!/usr/bin/env python3
"""
Hierarchical Circuit Generated from KiCad
"""

from circuit_synth import *


@circuit(name="child1")
def child1():
    """
    child1 subcircuit
    """

    # Create components
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )


@circuit(name="main")
def main():
    """
    Main circuit with hierarchical subcircuits
    """

    # Main circuit components
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Instantiate subcircuits
    child1_instance = child1()


# Generate the circuit
if __name__ == "__main__":
    circuit = main()
    circuit.generate_kicad_project(project_name="02_dual_hierarchy_generated")
