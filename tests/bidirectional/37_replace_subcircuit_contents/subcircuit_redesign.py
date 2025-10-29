#!/usr/bin/env python3
"""
Fixture: Subcircuit redesign test circuit.

Demonstrates subcircuit content replacement:
- Root circuit with main components
- Amplifier subcircuit with initial implementation (R1, C1)
- Test will modify the Amplifier subcircuit to use different components (R2, R3, C2)

Used to test replacing entire subcircuit implementation while preserving hierarchy.
"""

from circuit_synth import circuit, Component, Circuit


@circuit(name="subcircuit_redesign")
def subcircuit_redesign():
    """Root circuit with Amplifier subcircuit.

    Initial implementation:
    - Root: Main circuit with one component (e.g., signal source)
    - Amplifier: Subcircuit with R1 (10k), C1 (1µF) - simple RC filter

    The test will modify the Amplifier subcircuit to replace with new design.
    """
    from circuit_synth.core.decorators import get_current_circuit

    root = get_current_circuit()

    # Root circuit component
    main = Component(
        symbol="Device:R",
        ref="R_main",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    root.add_component(main)

    # Amplifier subcircuit - INITIAL IMPLEMENTATION
    # START_MARKER: Test will replace between these markers
    amplifier = Circuit("Amplifier")

    # Initial design: Simple RC filter (R1, C1)
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

    amplifier.add_component(r1)
    amplifier.add_component(c1)
    # END_MARKER

    root.add_subcircuit(amplifier)


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = subcircuit_redesign()

    circuit_obj.generate_kicad_project(
        project_name="subcircuit_redesign",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Subcircuit redesign circuit generated successfully!")
    print("📁 Open in KiCad: subcircuit_redesign/subcircuit_redesign.kicad_pro")
