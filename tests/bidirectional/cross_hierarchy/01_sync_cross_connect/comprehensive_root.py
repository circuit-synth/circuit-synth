#!/usr/bin/env python3
"""
Comprehensive root circuit for Test 38 - Connect across sheets.

Hierarchy:
- Root sheet with R1, R2
- Amplifier subcircuit with R3, R4
- Power supply subcircuit with R5, C2
- Will connect amplifier output to power supply input

Test operation: Add cross-sheet connection (amplifier → power_supply)
Expected: Cross-sheet connection created, all positions preserved
"""

from circuit_synth import circuit, Component, Net


@circuit(name="amplifier")
def amplifier_stage(input_sig, output_sig, vcc, gnd):
    """Amplifier subcircuit."""

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
    r3_amp[2] += output_sig

    r4_amp[1] += output_sig
    r4_amp[2] += gnd


@circuit(name="power_supply")
def power_supply(control_sig, vcc, gnd):
    """Power supply subcircuit."""

    r5_pwr = Component(
        symbol="Device:R",
        ref="R5",
        value="100",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    c2_pwr = Component(
        symbol="Device:C",
        ref="C2",
        value="10uF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    r5_pwr[1] += control_sig
    r5_pwr[2] += vcc

    c2_pwr[1] += control_sig
    c2_pwr[2] += gnd


@circuit(name="comprehensive_root")
def comprehensive_root():
    """Root circuit with two subcircuits connected across hierarchy."""

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
    sig_out = Net("SIG_OUT")  # Will be passed to power_supply as control_sig

    # Root connections
    r1[1] += sig_in
    r1[2] += vcc

    r2[1] += sig_out
    r2[2] += gnd

    # Hierarchical subcircuits
    amplifier_stage(input_sig=sig_in, output_sig=sig_out, vcc=vcc, gnd=gnd)
    power_supply(control_sig=sig_out, vcc=vcc, gnd=gnd)  # sig_out connects across sheets!


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
    print("  - Subcircuit 'power_supply': R5 (100), C2 (10uF)")
    print("  - Cross-sheet connection: sig_out connects amplifier → power_supply")
