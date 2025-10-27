#!/usr/bin/env python3
"""Single resistor circuit - starting point for test 04"""

from circuit_synth import *


@circuit
def main():
    """Single resistor test circuit"""

    # Create components
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )


# Generate the circuit
if __name__ == "__main__":
    circuit = main()
    # Generate KiCad project (creates directory)
    circuit.generate_kicad_project(project_name="main")
    # Generate KiCad netlist (required for ratsnest display)
    circuit.generate_kicad_netlist("main/main.net")
