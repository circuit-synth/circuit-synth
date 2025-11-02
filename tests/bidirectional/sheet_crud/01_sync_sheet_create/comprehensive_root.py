#!/usr/bin/env python3
"""
Comprehensive root circuit for Test 26 - Add hierarchical sheet.

Hierarchy:
- Root sheet with R1, R2
- Will add "power_supply" subcircuit sheet

Test operation: Add power_supply subcircuit with components
Expected: New sheet added, root sheet elements preserved
"""

from circuit_synth import circuit, Component, Net


# Uncomment to add power_supply subcircuit:
# @circuit(name="power_supply")
# def power_supply(vcc, gnd):
#     """Power supply subcircuit to be added."""
#
#     r_pwr = Component(
#         symbol="Device:R",
#         ref="R3",
#         value="100",
#         footprint="Resistor_SMD:R_0603_1608Metric"
#     )
#
#     c_pwr = Component(
#         symbol="Device:C",
#         ref="C1",
#         value="10uF",
#         footprint="Capacitor_SMD:C_0603_1608Metric"
#     )
#
#     r_pwr[1] += vcc
#     r_pwr[2] += gnd
#     c_pwr[1] += vcc
#     c_pwr[2] += gnd


@circuit(name="comprehensive_root")
def comprehensive_root():
    """Root circuit - will add power_supply subcircuit."""

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

    # Power
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # Root connections
    r1[1] += vcc
    r1[2] += gnd

    r2[1] += vcc
    r2[2] += gnd

    # Uncomment to add power_supply subcircuit:
    # power_supply(vcc=vcc, gnd=gnd)


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
    print("\n💡 Uncomment power_supply subcircuit to add new sheet")
