#!/usr/bin/env python3
"""Two resistor circuit - starting point for test 07"""

from circuit_synth import *


@circuit(name="two_resistors")
def two_resistors():
    """Circuit with two resistors for testing component deletion"""

    # Create components
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )


# Generate the circuit
if __name__ == "__main__":
    circuit = two_resistors()
    # Generate KiCad project (creates directory)
    circuit.generate_kicad_project(project_name="two_resistors")
    # Generate KiCad netlist (required for ratsnest display)
    circuit.generate_kicad_netlist("two_resistors/two_resistors.net")
