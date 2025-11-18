"""
Generate a simple schematic with a capacitor for property positioning reference.
"""

from circuit_synth import circuit, Component


@circuit(name="capacitor_reference")
def capacitor_test():
    """Single capacitor for property positioning analysis."""

    # Create a simple capacitor at a standard grid position
    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )


if __name__ == "__main__":
    import os

    # Generate the circuit
    print("Generating capacitor reference schematic...")
    circuit = capacitor_test()

    # Save to output directory
    output_dir = os.path.dirname(__file__)
    output_path = os.path.join(output_dir, "circuit_synth_generated")

    print(f"Writing KiCad project files to: {output_path}")
    circuit.generate_kicad_project(project_name=output_path)

    print(f"\nGenerated schematic: {output_path}.kicad_sch")
    print("Please open in KiCad to inspect component properties and text placement")
