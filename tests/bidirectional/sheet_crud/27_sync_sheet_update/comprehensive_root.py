#!/usr/bin/env python3
"""
Comprehensive root circuit for Test 27 - Update sheet properties.

Hierarchy:
- Root sheet with R1, R2
- Subcircuit "amplifier" with R3 (value will be changed)

Test operation: Update R3 value in amplifier subcircuit (demonstrates sheet content update)
Expected: Sheet content updated, all positions preserved
"""

from circuit_synth import circuit, Component, Net


@circuit(name="amplifier")
def amplifier_stage(input_sig, output_sig, vcc, gnd):
    """Amplifier subcircuit - R3 value will be updated."""

    r3_amp = Component(
        symbol="Device:R",
        ref="R3",
        value="1k",  # Will change to 2.2k
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r3_amp[1] += input_sig
    r3_amp[2] += output_sig


@circuit(name="comprehensive_root")
def comprehensive_root():
    """Root circuit with hierarchical amplifier subcircuit."""

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

    # Signal nets
    sig_in = Net("SIG_IN")
    sig_out = Net("SIG_OUT")

    # Root connections
    r1[1] += sig_in
    r1[2] += vcc

    r2[1] += sig_out
    r2[2] += gnd

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
    print("  - Root: R1 (10k), R2 (4.7k)")
    print("  - Subcircuit 'amplifier': R3 (1k)")
    print("  - Power: VCC, GND")
    print("  - Signals: SIG_IN, SIG_OUT")
    print("\n💡 Change R3 value from 1k to 2.2k to test")
