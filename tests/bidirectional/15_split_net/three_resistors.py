#!/usr/bin/env python3
"""
Fixture: Three resistors all connected via a single net.

Phase 1: All three resistors (R1, R2, R3) connected via NET1
This is used to:
1. Generate initial circuit with all 3 on single net
2. Verify netlist shows NET1 with 3 pins

To split the net, edit this file and move R3 to NET2:
- net1 = Net(name="NET1")
- net1 += r1[1]
- net1 += r2[1]
- (remove: net1 += r3[1])
-
- net2 = Net(name="NET2")
- net2 += r3[1]
"""

from circuit_synth import circuit, Component, Net


@circuit(name="three_resistors")
def three_resistors():
    """Circuit with three resistors all connected via NET1."""
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

    # Connect all three resistors via NET1
    net1 = Net(name="NET1")
    net1 += r1[1]
    net1 += r2[1]
    net1 += r3[1]


if __name__ == "__main__":
    circuit_obj = three_resistors()
    circuit_obj.generate_kicad_project(project_name="three_resistors")
    print("✅ Three resistors with NET1 connection generated!")
    print("📁 Open in KiCad: three_resistors/three_resistors.kicad_pro")
