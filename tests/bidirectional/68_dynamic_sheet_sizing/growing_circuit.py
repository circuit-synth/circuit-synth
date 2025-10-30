#!/usr/bin/env python3
"""
Fixture: Growing circuit for testing dynamic sheet sizing.

Initial: 10 resistors (fits on A4)
After modification: 60 resistors (requires A3 or larger)

Tests that KiCad schematic automatically resizes sheet to fit components.
"""

from circuit_synth import circuit, Component


@circuit(name="growing_circuit")
def growing_circuit():
    """Circuit that grows from 10 to 60 resistors.

    Initial state: R1-R10 (should fit on A4 sheet)
    Modified state: R1-R60 (should auto-resize to A3 or larger)
    """
    # Initial 10 resistors (A4 sheet)
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r4 = Component(
        symbol="Device:R",
        ref="R4",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r5 = Component(
        symbol="Device:R",
        ref="R5",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r6 = Component(
        symbol="Device:R",
        ref="R6",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r7 = Component(
        symbol="Device:R",
        ref="R7",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r8 = Component(
        symbol="Device:R",
        ref="R8",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r9 = Component(
        symbol="Device:R",
        ref="R9",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r10 = Component(
        symbol="Device:R",
        ref="R10",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # R11-R60 commented out - uncomment to test sheet resizing (50 more components)
    # When uncommented, sheet should automatically resize from A4 to A3 or larger

    # r11 = Component(symbol="Device:R", ref="R11", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r12 = Component(symbol="Device:R", ref="R12", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r13 = Component(symbol="Device:R", ref="R13", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r14 = Component(symbol="Device:R", ref="R14", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r15 = Component(symbol="Device:R", ref="R15", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r16 = Component(symbol="Device:R", ref="R16", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r17 = Component(symbol="Device:R", ref="R17", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r18 = Component(symbol="Device:R", ref="R18", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r19 = Component(symbol="Device:R", ref="R19", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r20 = Component(symbol="Device:R", ref="R20", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r21 = Component(symbol="Device:R", ref="R21", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r22 = Component(symbol="Device:R", ref="R22", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r23 = Component(symbol="Device:R", ref="R23", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r24 = Component(symbol="Device:R", ref="R24", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r25 = Component(symbol="Device:R", ref="R25", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r26 = Component(symbol="Device:R", ref="R26", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r27 = Component(symbol="Device:R", ref="R27", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r28 = Component(symbol="Device:R", ref="R28", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r29 = Component(symbol="Device:R", ref="R29", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r30 = Component(symbol="Device:R", ref="R30", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r31 = Component(symbol="Device:R", ref="R31", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r32 = Component(symbol="Device:R", ref="R32", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r33 = Component(symbol="Device:R", ref="R33", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r34 = Component(symbol="Device:R", ref="R34", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r35 = Component(symbol="Device:R", ref="R35", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r36 = Component(symbol="Device:R", ref="R36", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r37 = Component(symbol="Device:R", ref="R37", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r38 = Component(symbol="Device:R", ref="R38", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r39 = Component(symbol="Device:R", ref="R39", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r40 = Component(symbol="Device:R", ref="R40", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r41 = Component(symbol="Device:R", ref="R41", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r42 = Component(symbol="Device:R", ref="R42", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r43 = Component(symbol="Device:R", ref="R43", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r44 = Component(symbol="Device:R", ref="R44", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r45 = Component(symbol="Device:R", ref="R45", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r46 = Component(symbol="Device:R", ref="R46", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r47 = Component(symbol="Device:R", ref="R47", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r48 = Component(symbol="Device:R", ref="R48", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r49 = Component(symbol="Device:R", ref="R49", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r50 = Component(symbol="Device:R", ref="R50", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r51 = Component(symbol="Device:R", ref="R51", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r52 = Component(symbol="Device:R", ref="R52", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r53 = Component(symbol="Device:R", ref="R53", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r54 = Component(symbol="Device:R", ref="R54", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r55 = Component(symbol="Device:R", ref="R55", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r56 = Component(symbol="Device:R", ref="R56", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r57 = Component(symbol="Device:R", ref="R57", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r58 = Component(symbol="Device:R", ref="R58", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r59 = Component(symbol="Device:R", ref="R59", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    # r60 = Component(symbol="Device:R", ref="R60", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")


if __name__ == "__main__":
    circuit_obj = growing_circuit()

    circuit_obj.generate_kicad_project(
        project_name="growing_circuit",
        placement_algorithm="text_flow",
        generate_pcb=True,
    )

    print("✅ Growing circuit generated!")
    print("📁 Open in KiCad: growing_circuit/growing_circuit.kicad_pro")
    print()
    print("📏 Check sheet size:")
    print("   - File → Page Settings → should show current paper size")
    print("   - Initial: A4 (297×210mm) for 10 components")
    print("   - After adding R11-R60: Should auto-resize to A3 (420×297mm)")
