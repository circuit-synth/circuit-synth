#!/usr/bin/env python3
"""Circuit with two resistors, no connection."""

from circuit_synth import circuit, Component


@circuit(name="disconnected_resistors")
def disconnected_resistors():
    """Two resistors without connection."""
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

    # Net connection commented out (deleted)
    # net1 = Net("NET1")
    # net1.connect(r1["2"])
    # net1.connect(r2["1"])


if __name__ == "__main__":
    circuit_obj = disconnected_resistors()
    circuit_obj.generate_kicad_project(
        project_name="disconnected_resistors",
        placement_algorithm="simple",
        generate_pcb=True,
    )
