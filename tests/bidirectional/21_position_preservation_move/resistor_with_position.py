#!/usr/bin/env python3
"""Test position preservation when regenerating from Python"""
from circuit_synth import circuit, R


@circuit(name="resistor_with_position")
def resistor_with_position():
    """Single resistor for testing position preservation"""
    R("R1", value="10k", footprint="R_0603_1608Metric")


if __name__ == "__main__":
    circuit_obj = resistor_with_position()
    circuit_obj.generate_kicad_project(project_name="resistor_with_position")
