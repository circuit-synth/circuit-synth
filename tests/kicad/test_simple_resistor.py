"""Test script for simple resistor circuit generation."""

from circuit_synth import Component, Net, circuit


@circuit(name="simple_resistor")
def simple_resistor_circuit():
    """Simple test circuit with one resistor."""
    # Create a single resistor
    R1 = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Create nets
    VCC = Net("VCC")
    GND = Net("GND")

    # Connect resistor
    R1[1] += VCC
    R1[2] += GND

    return circuit()


if __name__ == "__main__":
    # Generate the circuit
    test_circuit = simple_resistor_circuit()

    # Generate KiCad project
    test_circuit.generate_kicad_project("simple_resistor")

    print("Simple resistor circuit generated successfully!")
