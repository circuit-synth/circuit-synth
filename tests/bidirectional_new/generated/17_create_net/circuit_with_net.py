#!/usr/bin/env python3
"""Circuit with two resistors connected."""

from circuit_synth import circuit, Component, Net


@circuit(name="connected_resistors")
def connected_resistors():
    """Two resistors with connection."""
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

    # Create net connecting R1 pin 2 to R2 pin 1
    net1 = Net("NET1")
    net1 += r1["2"]
    net1 += r2["1"]


if __name__ == "__main__":
    circuit_obj = connected_resistors()
    circuit_obj.generate_kicad_project(
        project_name="connected_resistors",
        placement_algorithm="simple",
        generate_pcb=True,
    )
