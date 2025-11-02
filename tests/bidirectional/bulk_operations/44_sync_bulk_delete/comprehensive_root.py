#!/usr/bin/env python3
"""
Comprehensive root circuit for Test 44 - Delete multiple components.

Root sheet:
- R1, R2, R3, R4, R5, C1, C2
- Will delete R3, R4, R5 in bulk

Test operation: Delete 3 components (R3, R4, R5)
Expected: Components removed, R1, R2, C1, C2 positions preserved
"""

from circuit_synth import circuit, Component, Net


@circuit(name="comprehensive_root")
def comprehensive_root():
    """Root circuit - will delete multiple components."""

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

    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )  # Will be deleted

    r4 = Component(
        symbol="Device:R",
        ref="R4",
        value="2.2k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )  # Will be deleted

    r5 = Component(
        symbol="Device:R",
        ref="R5",
        value="3.3k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )  # Will be deleted

    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    c2 = Component(
        symbol="Device:C",
        ref="C2",
        value="10uF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Power
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # Connections
    r1[1] += vcc
    r1[2] += gnd
    r2[1] += vcc
    r2[2] += gnd
    r3[1] += vcc  # Will be removed
    r3[2] += gnd  # Will be removed
    r4[1] += vcc  # Will be removed
    r4[2] += gnd  # Will be removed
    r5[1] += vcc  # Will be removed
    r5[2] += gnd  # Will be removed
    c1[1] += vcc
    c1[2] += gnd
    c2[1] += vcc
    c2[2] += gnd


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
    print("  - Root: R1 (10k), R2 (4.7k), R3 (1k), R4 (2.2k), R5 (3.3k), C1, C2")
    print("  - Power: VCC, GND")
    print("\n💡 Comment out R3, R4, R5 to delete 3 components in bulk")
