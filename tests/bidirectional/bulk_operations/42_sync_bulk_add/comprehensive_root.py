#!/usr/bin/env python3
"""
Comprehensive root circuit for Test 42 - Add multiple components.

Root sheet:
- R1, R2 initially
- Will add R3, R4, R5, C1, C2 in bulk

Test operation: Add 5 components at once (R3, R4, R5, C1, C2)
Expected: All new components added, R1/R2 positions preserved
"""

from circuit_synth import circuit, Component, Net


@circuit(name="comprehensive_root")
def comprehensive_root():
    """Root circuit - will add multiple components in bulk."""

    # Initial components
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

    # Components to be added:
    # r3 = Component(symbol="Device:R", ref="R3", value="1k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r4 = Component(symbol="Device:R", ref="R4", value="2.2k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r5 = Component(symbol="Device:R", ref="R5", value="3.3k", footprint="Resistor_SMD:R_0603_1608Metric")
    # c1 = Component(symbol="Device:C", ref="C1", value="100nF", footprint="Capacitor_SMD:C_0603_1608Metric")
    # c2 = Component(symbol="Device:C", ref="C2", value="10uF", footprint="Capacitor_SMD:C_0603_1608Metric")

    # Power
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # Root connections
    r1[1] += vcc
    r1[2] += gnd

    r2[1] += vcc
    r2[2] += gnd

    # Connections for new components:
    # r3[1] += vcc
    # r3[2] += gnd
    # r4[1] += vcc
    # r4[2] += gnd
    # r5[1] += vcc
    # r5[2] += gnd
    # c1[1] += vcc
    # c1[2] += gnd
    # c2[1] += vcc
    # c2[2] += gnd


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
    print("  - Root: R1 (10k), R2 (4.7k)")
    print("  - Power: VCC, GND")
    print("\n💡 Uncomment R3, R4, R5, C1, C2 to add 5 components in bulk")
