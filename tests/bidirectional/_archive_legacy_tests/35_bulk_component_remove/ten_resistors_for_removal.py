#!/usr/bin/env python3
"""
Fixture: Resistor array for testing bulk component removal.

Tests bulk component removal using Python loops - the advantage of circuit-synth!

Initial: 10 resistors (R1-R10) with varying values
Modified: 5 resistors (R1-R5) - remove R6-R10 by changing range

Real-world use case: Removing unused pull-up resistors, simplifying designs.
This demonstrates the power of Python for circuit generation.
"""

from circuit_synth import circuit, Component


@circuit(name="ten_resistors_for_removal")
def ten_resistors_for_removal():
    """Circuit with resistors created programmatically using Python loops.

    This is the advantage of circuit-synth Python - no need to manually
    delete repetitive component definitions!

    Initial: 10 resistors (R1-R10) with varying values
    Modified: 5 resistors (R1-R5) - change range(1, 11) to range(1, 6)
    """
    # Standard resistor E12 series values for variety
    resistor_values = [
        "10k",  # R1
        "4.7k",  # R2
        "2.2k",  # R3
        "1k",  # R4
        "100",  # R5
        "220",  # R6
        "470",  # R7
        "680",  # R8
        "1.5k",  # R9
        "3.3k",  # R10
    ]

    # Create resistors programmatically using Python loop
    # This is MUCH better than manually defining/deleting each one!
    resistors = []
    for i in range(1, 11):  # Change to range(1, 6) to remove R6-R10
        r = Component(
            symbol="Device:R",
            ref=f"R{i}",
            value=resistor_values[i - 1],  # Use corresponding value from list
            footprint="Resistor_SMD:R_0603_1608Metric",
        )
        resistors.append(r)

    # Return the list of resistors (optional - circuit decorator handles registration)
    return resistors


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = ten_resistors_for_removal()

    circuit_obj.generate_kicad_project(
        project_name="ten_resistors_for_removal",
        placement_algorithm="text_flow",
        generate_pcb=True,
    )

    print("✅ Resistor array generated successfully!")
    print(
        f"📁 Open in KiCad: ten_resistors_for_removal/ten_resistors_for_removal.kicad_pro"
    )
    print()
    print("💡 Python advantage demonstrated:")
    print("   - Created 10 resistors with varying values using a loop")
    print("   - To remove R6-R10: Just change range(1, 11) to range(1, 6)")
    print("   - No manual deletion of 5 component definitions!")
