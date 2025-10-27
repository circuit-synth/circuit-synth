#!/usr/bin/env python3
"""Circuit with power rails - GND and VCC."""

from circuit_synth import circuit, Component, Net


@circuit(name="power_rails")
def power_rails():
    """Three resistors with power rail connections."""
    # Create components
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

    # GND rail - all components connect pin 1 to ground
    gnd = Net("GND")
    gnd += r1["1"]
    gnd += r2["1"]
    gnd += r3["1"]

    # VCC rail - all components connect pin 2 to power
    vcc = Net("VCC")
    vcc += r1["2"]
    vcc += r2["2"]
    vcc += r3["2"]


if __name__ == "__main__":
    circuit_obj = power_rails()
    circuit_obj.generate_kicad_project(
        project_name="power_rails",
        placement_algorithm="simple",
        generate_pcb=True,
    )
