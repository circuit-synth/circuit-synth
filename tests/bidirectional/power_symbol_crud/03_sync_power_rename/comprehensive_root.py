#!/usr/bin/env python3
"""
Comprehensive root circuit for Test 36 - Rename power net.

Root sheet:
- R1, R2, C1
- VCC, GND power nets (will rename VCC to VBAT)

Test operation: Rename VCC power net to VBAT
Expected: Power symbol renamed, all positions preserved
"""

from circuit_synth import circuit, Component, Net


@circuit(name="comprehensive_root")
def comprehensive_root():
    """Root circuit - will rename VCC to VBAT."""

    # Root components
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
    vcc = Net(name="VCC")  # Will be renamed to VBAT
    gnd = Net(name="GND")

    # Root connections
    r1[1] += vcc
    r1[2] += gnd

    r2[1] += vcc
    r2[2] += gnd

    c1[1] += vcc
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
    print("  - Root: R1 (10k), R2 (4.7k), C1 (100nF)")
    print("  - Power: VCC, GND")
    print("\n💡 Rename VCC to VBAT to test power net rename")
