"""
Generate a simple schematic with 74LS245 for property positioning reference.
Testing wide 20-pin IC (level shifter).
"""

from circuit_synth import circuit, Component


@circuit(name="74ls245_reference")
def ic_74ls245_test():
    """Single 74LS245 for property positioning analysis."""

    # Create 74LS245 level shifter IC
    u1 = Component(
        symbol="74xx:74LS245",
        ref="U1",
        value="74HCT245",
        footprint="Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm"
    )


if __name__ == "__main__":
    import os

    # Generate the circuit
    print("Generating 74LS245 reference schematic...")
    circuit = ic_74ls245_test()

    # Save to output directory
    output_dir = os.path.dirname(__file__)
    output_path = os.path.join(output_dir, "circuit_synth_generated")

    print(f"Writing KiCad project files to: {output_path}")
    circuit.generate_kicad_project(project_name=output_path)

    print(f"\nGenerated schematic: {output_path}.kicad_sch")
    print("Please open in KiCad to inspect component properties and text placement")
