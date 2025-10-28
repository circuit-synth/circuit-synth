#!/usr/bin/env python3
"""
Fixture: Resistor divider for copy-paste component test.

Two-stage resistor divider used to test component duplication patterns:
- R1 and R2 in series
- VCC → R1[1]
- R1[2] → R2[1] (via Net1)
- R2[2] → GND

This serves as the base circuit that will be copy-pasted to create
R3 and R4 with similar connectivity patterns.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="resistor_divider_for_copy")
def resistor_divider_for_copy():
    """Circuit with resistor divider (R1-R2 in series with power and ground)."""

    # Create R1
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Create R2
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Net1: VCC → R1[1]
    net_vcc = Net(name="VCC")
    net_vcc += r1[1]

    # Net2: R1[2] → R2[1] (junction point)
    net_junction = Net(name="Net1")
    net_junction += r1[2]
    net_junction += r2[1]

    # Net3: R2[2] → GND
    net_gnd = Net(name="GND")
    net_gnd += r2[2]

    # R3 and R4 will be added by test (copy-paste pattern)
    # They will have similar structure:
    #   net_vcc_copy: VCC_copy → R3[1]
    #   net_junction_copy: Net2 → R3[2] and R4[1]
    #   net_gnd_copy: GND_copy → R4[2]


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = resistor_divider_for_copy()

    circuit_obj.generate_kicad_project(
        project_name="resistor_divider_for_copy",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Resistor divider circuit generated successfully!")
    print("📁 Open in KiCad: resistor_divider_for_copy/resistor_divider_for_copy.kicad_pro")
