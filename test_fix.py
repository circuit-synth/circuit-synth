#!/usr/bin/env python3
"""Test the reference display fix."""

from circuit_synth import Component, Circuit, Net, circuit

# Create a simple circuit with resistors to test reference display
@circuit
def test_circuit():
    # Create nets
    VCC = Net("VCC")
    GND = Net("GND")
    SIGNAL = Net("SIGNAL")
    
    # Create components
    R1 = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    R2 = Component(
        symbol="Device:R", 
        ref="R",
        value="20k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Connect components
    R1[1] += VCC
    R1[2] += SIGNAL
    
    R2[1] += SIGNAL
    R2[2] += GND
    
    # Position components
    R1.position = (50, 50)
    R2.position = (50, 70)
    
# Generate the KiCad files
if __name__ == "__main__":
    circ = test_circuit()
    circ.generate_kicad_project("test_reference_fix", generate_pcb=False)
    print("Generated test_reference_fix/test_reference_fix.kicad_sch")
    print("Check if references display as R1, R2 instead of R?, R?")