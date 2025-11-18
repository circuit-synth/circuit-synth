"""
Generate AMS1117-3.3 for property positioning reference.
Testing SOT-223 package (LDO voltage regulator).
"""

from circuit_synth import circuit, Component


@circuit(name="ams1117_reference")
def ams1117_test():
    """Single AMS1117-3.3 for property positioning analysis."""

    u1 = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U1",
        value="AMS1117-3.3",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )


if __name__ == "__main__":
    import os

    print("Generating AMS1117-3.3 reference schematic...")
    circuit = ams1117_test()

    output_dir = os.path.dirname(__file__)
    output_path = os.path.join(output_dir, "circuit_synth_generated")

    circuit.generate_kicad_project(project_name=output_path)
    print(f"Generated: {output_path}.kicad_sch")
