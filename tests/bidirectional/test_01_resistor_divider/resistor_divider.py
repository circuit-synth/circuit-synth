#!/usr/bin/env python3
"""
Single Resistor Circuit - Test Case 01
A simple circuit with two 1k resistors demonstrating proper reference assignment and net labeling
"""

import logging

from circuit_synth import Circuit, Component, Net, circuit

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
# Also set the circuit_synth logger specifically
logging.getLogger("circuit_synth").setLevel(logging.DEBUG)


@circuit(name="resistor_divider")
def create_resistor_divider_circuit():
    """Create a simple circuit with two resistors to demonstrate proper labeling"""
    # Create nets
    vin = Net("VIN")
    gnd = Net("GND")
    mid = Net("MID")  # Net connecting the two resistors

    # Create and add resistors with unique base references
    r1 = Component(
        symbol="Device:R",
        ref="R",  # Unique base reference
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r2 = Component(
        symbol="Device:R",
        ref="R",  # Unique base reference
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Connect resistors in series
    r1["1"] += vin  # Connect R1 pin 1 to VIN
    r1["2"] += mid  # Connect R1 pin 2 to MID
    r2["1"] += mid  # Connect R2 pin 1 to MID
    r2["2"] += gnd  # Connect R2 pin 2 to GND


# IMPORTANT: Create circuit at module level for validation
circuit_instance = create_resistor_divider_circuit()

if __name__ == "__main__":
    # Generate KiCad project (force create to ensure fresh generation)
    circuit_instance.generate_kicad_project("generated_resistor_divider")
