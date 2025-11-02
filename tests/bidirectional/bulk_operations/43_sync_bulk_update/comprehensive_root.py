#!/usr/bin/env python3
"""
Comprehensive root circuit for Test 43 - Update multiple components.

Root sheet:
- R1, R2, R3, R4, R5, C1, C2
- Will update values of R3, R4, R5 simultaneously

Test operation: Change values of R3 (1k→10k), R4 (2.2k→22k), R5 (3.3k→33k)
Expected: All values updated, all positions preserved
"""

from circuit_synth import circuit, Component, Net


@circuit(name="comprehensive_root")
def comprehensive_root():
    """Root circuit - will update multiple component values."""

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
        value="1k",  # Will change to 10k
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r4 = Component(
        symbol="Device:R",
        ref="R4",
        value="2.2k",  # Will change to 22k
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r5 = Component(
        symbol="Device:R",
        ref="R5",
        value="3.3k",  # Will change to 33k
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

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
    r3[1] += vcc
    r3[2] += gnd
    r4[1] += vcc
    r4[2] += gnd
    r5[1] += vcc
    r5[2] += gnd
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
    print("\n💡 Change R3→10k, R4→22k, R5→33k to test bulk update")
