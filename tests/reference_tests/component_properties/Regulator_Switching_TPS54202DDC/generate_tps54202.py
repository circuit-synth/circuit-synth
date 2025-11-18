"""
Generate TPS54202DDC for property positioning reference.
Testing SOT-23-6 package (buck converter).
"""

from circuit_synth import circuit, Component


@circuit(name="tps54202_reference")
def tps54202_test():
    """Single TPS54202DDC for property positioning analysis."""

    u1 = Component(
        symbol="Regulator_Switching:TPS54202DDC",
        ref="U1",
        value="TPS54202DDC",
        footprint="Package_TO_SOT_SMD:SOT-23-6"
    )


if __name__ == "__main__":
    import os

    print("Generating TPS54202DDC reference schematic...")
    circuit = tps54202_test()

    output_dir = os.path.dirname(__file__)
    output_path = os.path.join(output_dir, "circuit_synth_generated")

    circuit.generate_kicad_project(project_name=output_path)
    print(f"Generated: {output_path}.kicad_sch")
