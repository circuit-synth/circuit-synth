"""
Generate a simple schematic with MAX3485 for property positioning reference.
Testing SOIC-8 package (RS-485 transceiver).
"""

from circuit_synth import circuit, Component


@circuit(name="max3485_reference")
def max3485_test():
    """Single MAX3485 for property positioning analysis."""

    # Create MAX3485 RS-485 transceiver
    u1 = Component(
        symbol="Interface_UART:MAX3485",
        ref="U1",
        value="MAX485",
        footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
    )


if __name__ == "__main__":
    import os

    # Generate the circuit
    print("Generating MAX3485 reference schematic...")
    circuit = max3485_test()

    # Save to output directory
    output_dir = os.path.dirname(__file__)
    output_path = os.path.join(output_dir, "circuit_synth_generated")

    print(f"Writing KiCad project files to: {output_path}")
    circuit.generate_kicad_project(project_name=output_path)

    print(f"\nGenerated schematic: {output_path}.kicad_sch")
    print("Please open in KiCad to inspect component properties and text placement")
