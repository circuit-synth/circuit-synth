"""
Generate AO3401A for property positioning reference.
Testing SOT-23 package (P-channel MOSFET).
"""

from circuit_synth import circuit, Component


@circuit(name="ao3401a_reference")
def ao3401a_test():
    """Single AO3401A for property positioning analysis."""

    q1 = Component(
        symbol="Transistor_FET:AO3401A",
        ref="Q1",
        value="AO3401A",
        footprint="Package_TO_SOT_SMD:SOT-23"
    )


if __name__ == "__main__":
    import os

    print("Generating AO3401A reference schematic...")
    circuit = ao3401a_test()

    output_dir = os.path.dirname(__file__)
    output_path = os.path.join(output_dir, "circuit_synth_generated")

    circuit.generate_kicad_project(project_name=output_path)
    print(f"Generated: {output_path}.kicad_sch")
