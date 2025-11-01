#!/usr/bin/env python3
"""
Comprehensive root circuit for Test 15 - Update net connection preservation.

Contains components with nets:
- Components: R1 (10k), R2 (4.7k), C1 (100nF)
- Power: VCC, GND
- Nets: DATA (R1-R2), CLK (R2-C1)

Test operation: Change R2[2] from CLK to DATA (merge CLK into DATA)
Expected: R2[2] reconnected, all other connections preserved
"""

from circuit_synth import circuit, Component, Net


@circuit(name="comprehensive_root")
def comprehensive_root():
    """Comprehensive root circuit for net update testing."""

    # Components
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

    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Power
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # Signal nets
    data = Net("DATA")
    clk = Net("CLK")  # Will be merged into DATA in test

    # Connections
    r1[1] += data
    r1[2] += vcc

    r2[1] += data
    r2[2] += clk  # Will change to: r2[2] += data

    c1[1] += clk
    c1[2] += gnd


if __name__ == "__main__":
    circuit_obj = comprehensive_root()
    circuit_obj.generate_kicad_project(
        project_name="comprehensive_root",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )

    print("✅ Comprehensive root circuit generated!")
    print("📁 Open in KiCad: comprehensive_root/comprehensive_root.kicad_pro")
    print("\nCircuit contains:")
    print("  - R1 (10k), R2 (4.7k), C1 (100nF)")
    print("  - Power: VCC, GND")
    print("  - Nets: DATA (R1-R2), CLK (R2-C1)")
    print("\n💡 Change r2[2] from CLK to DATA to test net update")
