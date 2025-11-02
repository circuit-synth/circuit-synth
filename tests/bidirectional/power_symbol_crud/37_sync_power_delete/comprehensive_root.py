#!/usr/bin/env python3
"""
Comprehensive root circuit for Test 37 - Delete power symbol.

Root sheet:
- R1, R2, C1
- VCC, GND, +3V3 power nets (will delete +3V3)

Test operation: Delete +3V3 power net
Expected: Power symbol removed, other elements preserved
"""

from circuit_synth import circuit, Component, Net


@circuit(name="comprehensive_root")
def comprehensive_root():
    """Root circuit - will delete +3V3 power symbol."""

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
    vcc = Net(name="VCC")
    gnd = Net(name="GND")
    v3v3 = Net(name="+3V3")  # Will be deleted

    # Root connections
    r1[1] += vcc
    r1[2] += gnd

    r2[1] += vcc
    r2[2] += gnd

    c1[1] += v3v3  # Will be removed
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
    print("  - Power: VCC, GND, +3V3")
    print("\n💡 Delete +3V3 power net to test")
