#!/usr/bin/env python3
"""
Comprehensive root circuit for Test 40 - Move component between sheets.

Hierarchy:
- Root sheet with R1, R2, C1 (will move C1 to amplifier subcircuit)
- Amplifier subcircuit with R3, R4

Test operation: Move C1 from root to amplifier subcircuit
Expected: C1 appears in amplifier, removed from root, positions preserved

Note: "Moving" is implemented as: add C1 to amplifier, remove from root.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="amplifier")
def amplifier_stage(input_sig, output_sig, vcc, gnd):
    """Amplifier subcircuit - C1 will be added here."""

    r3_amp = Component(
        symbol="Device:R",
        ref="R3",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r4_amp = Component(
        symbol="Device:R",
        ref="R4",
        value="2.2k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # C1 will be added here:
    # c1 = Component(
    #     symbol="Device:C",
    #     ref="C1",
    #     value="100nF",
    #     footprint="Capacitor_SMD:C_0603_1608Metric"
    # )

    r3_amp[1] += input_sig
    r3_amp[2] += output_sig

    r4_amp[1] += output_sig
    r4_amp[2] += gnd

    # c1[1] += vcc
    # c1[2] += gnd


@circuit(name="comprehensive_root")
def comprehensive_root():
    """Root circuit - C1 will be moved to amplifier."""

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
    )  # Will be removed from root

    # Power
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # Signal nets
    sig_in = Net("SIG_IN")
    sig_out = Net("SIG_OUT")

    # Root connections
    r1[1] += sig_in
    r1[2] += vcc

    r2[1] += sig_out
    r2[2] += gnd

    c1[1] += vcc  # Will be removed
    c1[2] += gnd  # Will be removed

    # Hierarchical subcircuit
    amplifier_stage(input_sig=sig_in, output_sig=sig_out, vcc=vcc, gnd=gnd)


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
    print("  - Subcircuit 'amplifier': R3 (1k), R4 (2.2k)")
    print("\n💡 Move C1 from root to amplifier: uncomment in amplifier, comment in root")
