#!/usr/bin/env python3
"""
Comprehensive root circuit for Test 17 - Delete net preservation.

Contains components with nets:
- Components: R1 (10k), R2 (4.7k), C1 (100nF)
- Power: VCC, GND
- Nets: DATA (R1-C1), CLK (R2)

Test operation: Delete CLK net
Expected: CLK removed, DATA and all other elements preserved
"""

from circuit_synth import circuit, Component, Net


@circuit(name="comprehensive_root")
def comprehensive_root():
    """Comprehensive root circuit for net deletion testing."""

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
    clk = Net("CLK")  # Will be deleted in test

    # Connections
    r1[1] += data
    r1[2] += vcc

    r2[1] += clk  # Will be disconnected when CLK deleted
    r2[2] += gnd

    c1[1] += data
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
    print("  - Nets: DATA (R1-C1), CLK (R2)")
    print("\n💡 Delete CLK net (comment out clk and r2[1] connection) to test")
