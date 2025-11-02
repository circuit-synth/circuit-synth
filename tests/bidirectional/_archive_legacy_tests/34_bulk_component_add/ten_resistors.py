#!/usr/bin/env python3
"""
Fixture: Resistor array created programmatically.

Tests bulk component addition using Python loops - the advantage of circuit-synth!

Initial: 10 resistors (R1-R10)
Modified: 20 resistors (R1-R20)

Real-world use case: Pull-up/pull-down resistor banks, termination networks.
This demonstrates the power of Python for circuit generation.
"""

from circuit_synth import circuit, Component


@circuit(name="ten_resistors")
def ten_resistors():
    """Circuit with resistors created programmatically using Python loops.

    This is the advantage of circuit-synth Python - no need to manually
    write repetitive component definitions!

    Initial: 10 resistors (R1-R10)
    Modified: 20 resistors (R1-R20) - change range(1, 11) to range(1, 21)
    """
    # Create resistors programmatically using Python loop
    # This is MUCH better than manually defining each one!
    resistors = []
    for i in range(1, 11):  # Change to range(1, 21) to add 10 more
        r = Component(
            symbol="Device:R",
            ref=f"R{i}",
            value="10k",
            footprint="Resistor_SMD:R_0603_1608Metric",
        )
        resistors.append(r)

    # Return the list of resistors (optional - circuit decorator handles registration)
    return resistors


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = ten_resistors()

    circuit_obj.generate_kicad_project(
        project_name="ten_resistors",
        placement_algorithm="text_flow",
        generate_pcb=True,
    )

    print("✅ Resistor array generated successfully!")
    print(f"📁 Open in KiCad: ten_resistors/ten_resistors.kicad_pro")
    print()
    print("💡 Python advantage demonstrated:")
    print("   - Created 10 resistors with 5 lines of code (loop)")
    print("   - To add 10 more: Just change range(1, 11) to range(1, 21)")
    print("   - No manual copy-paste of 87 lines of code!")
