#!/usr/bin/env python3
"""
Simple test circuit with a single resistor to debug reference designator issue
"""
from circuit_synth import *

@circuit(name='singe_resistor_generated')
def create_single_resistor():
    """Test circuit with just one resistor"""

    
    # Create a single resistor
    R = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    child1()

@circuit(name='chil1')
def child1():
    """Test circuit with just one resistor"""

    
    # Create a single resistor
    R = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    child2()

@circuit(name='child2')
def child2():
    """Test circuit with just one resistor"""

    
    # Create a single resistor
    R = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    

if __name__ == "__main__":
    # Generate the circuit
    circuit_obj = create_single_resistor()
    
    # Generate KiCad files
    circuit_obj.generate_kicad_project(
        "single_resistor_generated"
    )
    
    print("Generated KiCad project in single_resistor_generated/")