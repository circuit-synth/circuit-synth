#!/usr/bin/env python3
"""
Comprehensive root circuit for Test 45 - Complex multi-operation workflow.

Hierarchy:
- Root sheet with R1, R2, C1
- Amplifier subcircuit with R3, R4

Workflow will perform:
1. Add R5 to root
2. Update R2 value (4.7k → 47k)
3. Delete C1 from root
4. Rename VCC to VBAT
5. Add C2 to amplifier subcircuit

Test operation: Multiple CRUD operations in one workflow
Expected: All operations applied correctly, all positions preserved
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

    # C2 will be added:
    # c2_amp = Component(
    #     symbol="Device:C",
    #     ref="C2",
    #     value="10uF",
    #     footprint="Capacitor_SMD:C_0603_1608Metric"
    # )

    r3_amp[1] += input_sig
    r3_amp[2] += output_sig

    r4_amp[1] += output_sig
    r4_amp[2] += gnd

    # c2_amp[1] += vcc
    # c2_amp[2] += gnd


@circuit(name="comprehensive_root")
def comprehensive_root():
    """Root circuit - complex workflow test."""

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
        value="4.7k",  # Will change to 47k
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )  # Will be deleted

    # R5 will be added:
    # r5 = Component(
    #     symbol="Device:R",
    #     ref="R5",
    #     value="100k",
    #     footprint="Resistor_SMD:R_0603_1608Metric"
    # )

    # Power
    vcc = Net(name="VCC")  # Will be renamed to VBAT
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

    # r5[1] += vcc  # Will be added
    # r5[2] += gnd  # Will be added

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
    print("  - Power: VCC, GND")
    print("\nWorkflow: Add R5, Update R2→47k, Delete C1, Rename VCC→VBAT, Add C2 to amplifier")
