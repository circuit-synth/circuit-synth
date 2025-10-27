from circuit_synth import *


@circuit(name="top_level")
def top_level():
    """Top level circuit"""

    # Create components
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0805_2012Metric",
    )
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0805_2012Metric",
    )
    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="10k",
        footprint="Resistor_SMD:R_0805_2012Metric",
    )
    r4 = Component(
        symbol="Device:R",
        ref="R4",
        value="10k",
        footprint="Resistor_SMD:R_0805_2012Metric",
    )


def main():
    circuit = top_level()
    circuit.generate_kicad_project("test_project")


if __name__ == "__main__":
    main()
