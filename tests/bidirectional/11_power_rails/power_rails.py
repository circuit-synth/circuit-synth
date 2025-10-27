#!/usr/bin/env python3
"""
Fixture: Power rail circuit with GND and VCC.

Tests power rail distribution - multiple components sharing GND and VCC connections.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="power_rails")
def power_rails():
    """Circuit with three resistors sharing GND and VCC power rails."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="2.2k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Create GND and VCC power rails
    gnd = Net(name="GND")
    vcc = Net(name="VCC")

    # Connect all components to GND
    gnd.connect(r1[2])
    gnd.connect(r2[2])
    gnd.connect(r3[2])

    # Connect all components to VCC
    vcc.connect(r1[1])
    vcc.connect(r2[1])
    vcc.connect(r3[1])


if __name__ == "__main__":
    circuit_obj = power_rails()
    circuit_obj.generate_kicad_project(
        project_name="power_rails",
        placement_algorithm="simple",
        generate_pcb=True
    )
    print("✅ Power rails circuit generated!")
    print("📁 Open in KiCad: power_rails/power_rails.kicad_pro")
