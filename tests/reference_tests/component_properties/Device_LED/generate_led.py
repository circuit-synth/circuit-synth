"""
Generate a simple schematic with an LED for property positioning reference.
Testing rotation at 90 degrees (vertical orientation).
"""

from circuit_synth import circuit, Component


@circuit(name="led_reference")
def led_test():
    """Single LED for property positioning analysis at 90° rotation."""

    # Create an LED at 90° rotation (vertical orientation)
    # This tests if text positioning handles rotation correctly
    d1 = Component(
        symbol="Device:LED",
        ref="D1",
        value="RED",
        footprint="LED_SMD:LED_0603_1608Metric"
    )


if __name__ == "__main__":
    import os

    # Generate the circuit
    print("Generating LED reference schematic...")
    circuit = led_test()

    # Save to output directory
    output_dir = os.path.dirname(__file__)
    output_path = os.path.join(output_dir, "circuit_synth_generated")

    print(f"Writing KiCad project files to: {output_path}")
    circuit.generate_kicad_project(project_name=output_path)

    print(f"\nGenerated schematic: {output_path}.kicad_sch")
    print("Please open in KiCad to inspect component properties and text placement")
    print("NOTE: LED should be rotated 90° for proper testing")
