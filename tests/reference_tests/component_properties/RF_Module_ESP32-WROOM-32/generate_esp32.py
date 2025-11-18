"""
Generate a simple schematic with ESP32-WROOM-32 for property positioning reference.
Testing large microprocessor module with many pins.
"""

from circuit_synth import circuit, Component


@circuit(name="esp32_reference")
def esp32_test():
    """Single ESP32-WROOM-32 for property positioning analysis."""

    # Create ESP32 module
    u1 = Component(
        symbol="RF_Module:ESP32-WROOM-32",
        ref="U1",
        value="ESP32-WROOM-32",
        footprint="RF_Module:ESP32-WROOM-32"
    )


if __name__ == "__main__":
    import os

    # Generate the circuit
    print("Generating ESP32-WROOM-32 reference schematic...")
    circuit = esp32_test()

    # Save to output directory
    output_dir = os.path.dirname(__file__)
    output_path = os.path.join(output_dir, "circuit_synth_generated")

    print(f"Writing KiCad project files to: {output_path}")
    circuit.generate_kicad_project(project_name=output_path)

    print(f"\nGenerated schematic: {output_path}.kicad_sch")
    print("Please open in KiCad to inspect component properties and text placement")
