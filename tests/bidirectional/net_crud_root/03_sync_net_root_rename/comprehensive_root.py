#!/usr/bin/env python3
"""
Comprehensive root circuit for Test 16 - Rename net preservation.

Contains components with nets:
- Components: R1 (10k), R2 (4.7k), C1 (100nF)
- Power: VCC, GND
- Nets: DATA (R1-R2-C1)

Test operation: Rename DATA → SIG
Expected: Net renamed, all connections and positions preserved
"""

from circuit_synth import circuit, Component, Net


@circuit(name="comprehensive_root")
def comprehensive_root():
    """Comprehensive root circuit for net rename testing."""

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

    # Signal net (will be renamed to SIG in test)
    data = Net("DATA")

    # Connections
    r1[1] += data
    r1[2] += vcc

    r2[1] += data
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
    print("  - Net: DATA (R1-R2-C1)")
    print("\n💡 Rename 'data = Net(\"DATA\")' to 'sig = Net(\"SIG\")' to test")
