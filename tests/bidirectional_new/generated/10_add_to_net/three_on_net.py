#!/usr/bin/env python3
"""Three resistors connected to same net."""

from circuit_synth import circuit, Component, Net


@circuit(name="three_resistors_net")
def three_resistors_net():
    """Three resistors on NET1."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="20k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="30k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # All three components on same net
    net1 = Net("SHARED_NET")
    net1 += r1["2"]
    net1 += r2["1"]
    net1 += r3["1"]  # R3 added to existing net


if __name__ == "__main__":
    circuit_obj = three_resistors_net()
    circuit_obj.generate_kicad_project(
        project_name="three_resistors_net",
        placement_algorithm="simple",
        generate_pcb=True,
    )
