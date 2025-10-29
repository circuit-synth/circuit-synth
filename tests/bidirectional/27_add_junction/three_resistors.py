#!/usr/bin/env python3
"""
Fixture: Three resistors in T-connection (junction required).

Phase 1: T-connection where R2's pin splits to connect both R1 and R3
- Creates a three-way connection point requiring a junction dot
- All three pins are on the same net (NET1)
- Junction appears visually to clarify the connection

To modify to Y-connection, edit this file and create separate nets:
- net1 = Net(name="NET1")
- net1 += r1[1]
- net1 += r2[1]
-
- net2 = Net(name="NET2")
- net2 += r3[1]
"""

from circuit_synth import circuit, Component, Net


@circuit(name="three_resistors")
def three_resistors():
    """Circuit with three resistors in T-connection (junction required)."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="2.2k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # T-connection: all three resistors connected via NET1
    # This creates a three-way junction at one point requiring a junction dot
    net1 = Net(name="NET1")
    net1 += r1[1]
    net1 += r2[1]
    net1 += r3[1]


if __name__ == "__main__":
    circuit_obj = three_resistors()
    circuit_obj.generate_kicad_project(project_name="three_resistors")
    print("✅ Three resistors with T-connection (NET1) generated!")
    print("📁 Open in KiCad: three_resistors/three_resistors.kicad_pro")
    print("🔍 Look for junction dot at connection point where R1, R2, R3 meet")
