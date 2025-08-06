#!/usr/bin/env python3
"""
Test script for improved component placement with accurate bounding boxes.
"""
import logging

from circuit_synth import Circuit, Component, Net, circuit

# Set up logging to see debug output
logging.basicConfig(
    level=logging.DEBUG, format="%(name)s - %(levelname)s - %(message)s"
)


@circuit
def create_placement_test_circuit():
    """Create a test circuit with various component types to verify improved placement."""
    # Power supply
    vcc = Net("VCC")
    gnd = Net("GND")

    # Add various component types
    # Resistors (should be 200x750 mil = 5.08x19.05 mm)
    r1 = Component("Device:R", ref="R1", value="10k")
    r2 = Component("Device:R", ref="R2", value="4.7k")
    r3 = Component("Device:R", ref="R3", value="1k")

    # Capacitors (should be 200x750 mil = 5.08x19.05 mm)
    c1 = Component("Device:C", ref="C1", value="100nF")
    c2 = Component("Device:C", ref="C2", value="10uF")

    # Thermistor (should be 300x850 mil = 7.62x21.59 mm)
    th1 = Component("Device:Thermistor", ref="TH1", value="10k")

    # Voltage regulator (larger component)
    u1 = Component("Regulator_Linear:LM7805_TO220", ref="U1", value="LM7805")

    # Components are automatically added to the circuit
    # Create some connections
    r1["1"] += vcc
    r1["2"] += r2["1"]
    r2["1"] += c1["1"]
    r2["2"] += gnd
    c1["2"] += gnd

    u1["VI"] += vcc
    u1["GND"] += gnd
    u1["VO"] += r3["1"]
    r3["1"] += c2["1"]
    r3["2"] += th1["1"]
    th1["2"] += gnd
    c2["2"] += gnd


def test_placement_circuit():
    """Test that placement circuit can be created successfully."""
    circuit = create_placement_test_circuit()
    assert circuit is not None
    assert circuit.name == "create_placement_test_circuit"
    assert len(circuit.components) > 0
    assert len(circuit.nets) > 0


def main():
    """Generate the test circuit and create KiCad project."""
    print("Testing improved component placement with accurate bounding boxes...")

    # Create the circuit
    circuit = create_placement_test_circuit()

    # Generate KiCad project
    output_dir = "test_improved_placement_output"

    print(f"\nGenerating KiCad project in: {output_dir}")
    circuit.generate_kicad_project(
        path=output_dir, project_name="test_improved_placement", force_create=True
    )

    print("\nDone! Check the generated schematic to verify:")
    print("1. Components should have tighter spacing")
    print("2. Resistors and capacitors should use actual 5.08x19.05mm bounds")
    print("3. Thermistor should use 7.62x21.59mm bounds")
    print("4. Text width should be calculated based on character count")
    print("5. No overlapping labels")

    print(
        f"\nOpen the schematic with: kicad {output_dir}/test_improved_placement.kicad_pro"
    )


if __name__ == "__main__":
    main()
