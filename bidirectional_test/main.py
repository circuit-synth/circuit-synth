#!/usr/bin/env python3
from circuit_synth import *


@circuit(name="BidirectionalTest")
def main():
    """Bidirectional sync test circuit"""

    # Create components



    # Create components
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
if __name__ == "__main__":
    circuit_obj = main()
    circuit_obj.generate_kicad_project(
        project_name="BidirectionalTest",
        placement_algorithm="hierarchical",
        generate_pcb=True,
    )
    print("Generated BidirectionalTest/")