#!/usr/bin/env python3
"""
Fixture: Subcircuit redesign test circuit.

Demonstrates subcircuit content replacement:
- Root circuit with main components
- Amplifier subcircuit with initial implementation (R1, C1)
- Test will modify the Amplifier subcircuit to use different components (R2, R3, C2)

Used to test replacing entire subcircuit implementation while preserving hierarchy.
"""

from circuit_synth import circuit, Component, Net


@circuit
def amplifier_subcircuit():
    """Amplifier subcircuit that can be redesigned.

    Initial implementation: Simple RC filter (R1, C1)
    Modified implementation: Multi-stage filter (R2, R3, C2)
    """
    # Initial design: Simple RC filter (R1, C1)
    # Uncomment these lines for initial state:
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="1µF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )

    # Modified design: New implementation (R2, R3, C2)
    # Uncomment these lines for modified state:
    # r2 = Component(
    #     symbol="Device:R",
    #     ref="R2",
    #     value="22k",
    #     footprint="Resistor_SMD:R_0603_1608Metric",
    # )
    # r3 = Component(
    #     symbol="Device:R",
    #     ref="R3",
    #     value="47k",
    #     footprint="Resistor_SMD:R_0603_1608Metric",
    # )
    # c2 = Component(
    #     symbol="Device:C",
    #     ref="C2",
    #     value="10µF",
    #     footprint="Capacitor_SMD:C_0603_1608Metric",
    # )


@circuit(name="subcircuit_redesign")
def subcircuit_redesign():
    """Root circuit with Amplifier subcircuit.

    Root: Main resistor (R_main)
    Subcircuit: Amplifier (R1, C1 → R2, R3, C2)
    """
    # Root circuit component
    main = Component(
        symbol="Device:R",
        ref="R_main1",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Call subcircuit - creates hierarchical sheet
    amplifier_subcircuit()


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = subcircuit_redesign()

    circuit_obj.generate_kicad_project(project_name="subcircuit_redesign")

    print("✅ Subcircuit redesign circuit generated successfully!")
    print("📁 Open in KiCad: subcircuit_redesign/subcircuit_redesign.kicad_pro")
