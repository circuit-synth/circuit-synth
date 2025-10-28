#!/usr/bin/env python3
"""
Fixture: Ten resistors in a grid pattern.

Tests bulk component addition - 10 resistors placed in a 2x5 grid.
R1-R10 are standard, R11 is commented out for testing addition workflow.

Real-world use case: Pull-up/pull-down resistor banks, termination networks.
"""

from circuit_synth import circuit, Component


@circuit(name="ten_resistors")
def ten_resistors():
    """Circuit with 10 resistors arranged in a 2x5 grid."""
    # Column 1: R1, R3, R5, R7, R9
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r5 = Component(
        symbol="Device:R",
        ref="R5",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r7 = Component(
        symbol="Device:R",
        ref="R7",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r9 = Component(
        symbol="Device:R",
        ref="R9",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Column 2: R2, R4, R6, R8, R10
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r4 = Component(
        symbol="Device:R",
        ref="R4",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r6 = Component(
        symbol="Device:R",
        ref="R6",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r8 = Component(
        symbol="Device:R",
        ref="R8",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r10 = Component(
        symbol="Device:R",
        ref="R10",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # R11 commented out - used for testing bulk component addition
    # r11 = Component(
    #     symbol="Device:R",
    #     ref="R11",
    #     value="10k",
    #     footprint="Resistor_SMD:R_0603_1608Metric",
    # )


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = ten_resistors()

    circuit_obj.generate_kicad_project(
        project_name="ten_resistors",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Ten resistors circuit generated successfully!")
    print("📁 Open in KiCad: ten_resistors/ten_resistors.kicad_pro")
