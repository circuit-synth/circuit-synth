#!/usr/bin/env python3
"""
Comprehensive root circuit for Test 35 - Change power symbol type.

Root sheet:
- R1, R2, C1
- VCC, GND, +3V3 power nets (will change +3V3 to +5V)

Test operation: Change +3V3 power net to +5V
Expected: Power symbol type updated, all positions preserved
"""

from circuit_synth import circuit, Component, Net


@circuit(name="comprehensive_root")
def comprehensive_root():
    """Root circuit - will change +3V3 to +5V."""

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
    v3v3 = Net(name="+3V3")  # Will be changed to +5V

    # Root connections
    r1[1] += vcc
    r1[2] += gnd

    r2[1] += vcc
    r2[2] += gnd

    c1[1] += v3v3
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
    print("\n💡 Change +3V3 to +5V to test power symbol type change")
