#!/usr/bin/env python3
"""Single resistor for testing canonical rename detection"""

from circuit_synth import *


@circuit(name="single_resistor")
def single_resistor():
    """Circuit with one resistor for canonical rename testing"""

    # Create component
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )


# Generate the circuit
if __name__ == "__main__":
    circuit = single_resistor()
    circuit.generate_kicad_project(project_name="single_resistor")
    circuit.generate_kicad_netlist("single_resistor/single_resistor.net")
