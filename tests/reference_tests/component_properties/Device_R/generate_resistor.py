"""
Generate a simple schematic with a resistor for property positioning reference.

This script creates a minimal schematic with a single resistor to compare
circuit-synth generated output against manually placed KiCad components.
"""

from circuit_synth import circuit, Component


@circuit(name="resistor_reference")
def resistor_test():
    """Single resistor for property positioning analysis."""

    # Create a simple resistor at a standard grid position
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )


if __name__ == "__main__":
    import os

    # Generate the circuit
    print("Generating resistor reference schematic...")
    circuit = resistor_test()

    # Save to output directory
    output_dir = os.path.dirname(__file__)
    output_path = os.path.join(output_dir, "circuit_synth_generated")

    print(f"Writing KiCad project files to: {output_path}")
    circuit.generate_kicad_project(project_name=output_path)

    print(f"\nGenerated schematic: {output_path}.kicad_sch")
    print("Please open in KiCad to inspect component properties and text placement")
