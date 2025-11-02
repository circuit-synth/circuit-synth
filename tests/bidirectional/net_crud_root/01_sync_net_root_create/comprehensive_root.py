#!/usr/bin/env python3
"""
Comprehensive root circuit for Test 14 - Add net preservation.

Contains components initially disconnected:
- Components: R1 (10k), R2 (4.7k), C1 (100nF)
- Power: VCC, GND
- Initial: R2 is isolated (no connections except power)
- Test operation: Add CLK net connecting R2-C1

Expected: CLK net added, all other elements preserved
"""

from circuit_synth import circuit, Component, Net


@circuit(name="comprehensive_root")
def comprehensive_root():
    """Comprehensive root circuit for net addition testing."""

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
    # clk = Net("CLK")  # Will be added in test

    # Connections
    r1[1] += data
    r1[2] += vcc

    # R2 connected to power only (isolated from signals initially)
    r2[1] += vcc
    # r2[2] will be connected to CLK in test

    # C1 connected to GND only (isolated initially)
    c1[2] += gnd
    # c1[1] will be connected to CLK in test


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
    print("  - Net: DATA (R1 only)")
    print("  - R2 and C1 initially isolated from signals")
    print("\n💡 Add CLK net connecting R2-C1 to test preservation")
