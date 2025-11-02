#!/usr/bin/env python3
"""
Test fixture: Duplicate net names in separate circuits should NOT connect.

Validates the critical safety property that:
- Each @circuit function creates isolated net namespace
- Net("SIGNAL") in circuit_a is different from Net("SIGNAL") in circuit_b
- Components only connect within their own circuit
- No implicit global nets - all cross-circuit connections must be explicit

This prevents dangerous bugs where same net names accidentally connect unrelated circuits.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="circuit_a")
def circuit_a():
    """First circuit with its own Net("SIGNAL")."""
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

    # Circuit A's SIGNAL net - connects R1 and R2
    signal = Net("SIGNAL")
    r1[1] += signal
    r2[1] += signal


@circuit(name="circuit_b")
def circuit_b():
    """Second circuit with SAME net name "SIGNAL" (but different instance)."""
    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r4 = Component(
        symbol="Device:R",
        ref="R4",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Circuit B's SIGNAL net - DIFFERENT from circuit_a's SIGNAL
    # Even though name is same, this is a separate Net instance
    signal = Net("SIGNAL")
    r3[1] += signal
    r4[1] += signal


@circuit(name="main")
def main():
    """Main circuit that instantiates both circuit_a and circuit_b."""
    # Both circuits have Net("SIGNAL") but they should NOT connect!
    circuit_a()
    circuit_b()


if __name__ == "__main__":
    # Generate KiCad project
    circuit_obj = main()

    circuit_obj.generate_kicad_project(
        project_name="isolated_circuits",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Circuits with duplicate net names generated!")
    print("📁 Open in KiCad: isolated_circuits/isolated_circuits.kicad_pro")
    print("")
    print("Expected behavior:")
    print("  - R1—R2 connected (circuit_a's SIGNAL)")
    print("  - R3—R4 connected (circuit_b's SIGNAL)")
    print("  - R1 NOT connected to R3 (separate net instances)")
