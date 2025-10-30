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
    """Circuit that grows from 10 to 60 resistors using Python loops.

    This demonstrates the power of circuit-synth Python - use loops instead
    of manually defining 60 components!

    Initial state: R1-R10 (should fit on A4 sheet)
    Modified state: R1-R60 (should auto-resize to A3 or larger)
    """
    # Create resistors programmatically using Python loop
    # This is the advantage of circuit-synth!
    resistors = []
    for i in range(1, 11):  # Change to range(1, 61) to add 50 more
        r = Component(
            symbol="Device:R",
            ref=f"R{i}",
            value="10k",
            footprint="Resistor_SMD:R_0603_1608Metric",
        )
        resistors.append(r)

    return resistors


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
    print("💡 Python advantage demonstrated:")
    print("   - Created resistors with simple loop: for i in range(1, 11)")
    print("   - To add 50 more: Just change to range(1, 61)")
    print("   - No manual copy-paste of 50 component definitions!")
    print()
    print("📏 Check sheet size:")
    print("   - File → Page Settings → should show current paper size")
    print("   - Initial: A4 (297×210mm) for 10 components")
    print("   - After changing to range(1, 61): Should auto-resize to A3 (420×297mm)")
