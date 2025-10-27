#!/usr/bin/env python3
"""
Circuit Generated from KiCad
"""

from circuit_synth import *

@circuit
def main():
    """Generated circuit from KiCad"""

    # Create components
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="20k", footprint="Resistor_SMD:R_0603_1608Metric")

    # Added in iteration 2
    c1 = Component(symbol="Device:C", ref="C1", value="100nF", footprint="Capacitor_SMD:C_0603_1608Metric")


# Generate the circuit
if __name__ == '__main__':
    circuit = main()
    # Generate KiCad project (creates directory)
    circuit.generate_kicad_project(project_name="growing_circuit_generated")
    # Generate KiCad netlist (required for ratsnest display)
    circuit.generate_kicad_netlist("growing_circuit_generated/growing_circuit_generated.net")