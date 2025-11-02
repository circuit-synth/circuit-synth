#!/usr/bin/env python3
"""
Comprehensive root circuit for Test 41 - Propagate changes up/down hierarchy.

Hierarchy:
- Root sheet with R1, R2
- Amplifier subcircuit with R3, R4
- Will change VCC net name, which should propagate to subcircuit

Test operation: Rename VCC to VBAT (should propagate through hierarchy)
Expected: Name change propagates to all sheets, all positions preserved
"""

from circuit_synth import circuit, Component, Net


@circuit(name="amplifier")
def amplifier_stage(input_sig, output_sig, vcc, gnd):
    """Amplifier subcircuit - vcc parameter will be VBAT after rename."""

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

    r3_amp[1] += input_sig
    r3_amp[2] += vcc  # vcc will become VBAT

    r4_amp[1] += output_sig
    r4_amp[2] += gnd


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

    # Power
    vcc = Net(name="VCC")  # Will be renamed to VBAT
    gnd = Net(name="GND")

    # Signal nets
    sig_in = Net("SIG_IN")
    sig_out = Net("SIG_OUT")

    # Root connections
    r1[1] += sig_in
    r1[2] += vcc  # Will become VBAT

    r2[1] += sig_out
    r2[2] += gnd

    # Hierarchical subcircuit - vcc parameter will propagate name change
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
    print("  - Subcircuit 'amplifier': R3 (1k), R4 (2.2k)")
    print("  - Power: VCC, GND")
    print("\n💡 Rename VCC to VBAT - change should propagate to amplifier subcircuit")
