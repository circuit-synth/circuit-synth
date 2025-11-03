#!/usr/bin/env python3
"""
Comprehensive root circuit for preservation testing.

Contains ALL schematic element types:
- Components: R1 (10k), C1 (100nF)
- Power: VCC, GND
- Nets: DATA (connects R1-C1)

Note: R2 is commented out initially for the "add component" test.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="comprehensive_root")
def comprehensive_root():
    """Comprehensive root circuit with multiple element types."""

    # Components
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # r2 = Component(
    #     symbol="Device:R",
    #     ref="R2",
    #     value="4.7k",
    #     footprint="Resistor_SMD:R_0603_1608Metric",
    # )

    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )

    # Power
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # Signal nets
    data = Net("DATA")

    # Connections
    r1[1] += data
    c1[1] += data
    # r2[1] += data

    r1[2] += vcc
    c1[2] += gnd
    # r2[2] += gnd


if __name__ == "__main__":
    circuit_obj = comprehensive_root()
    circuit_obj.generate_kicad_project(
        project_name="comprehensive_root",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Comprehensive root circuit generated!")
    print("📁 Open in KiCad: comprehensive_root/comprehensive_root.kicad_pro")
    print("\nCircuit contains:")
    print("  - R1 (10k), C1 (100nF)")
    print("  - Power: VCC, GND")
    print("  - Net: DATA (R1-C1)")
    print("\n💡 R2 is commented out - uncomment to test adding component")
