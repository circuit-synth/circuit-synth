#!/usr/bin/env python3
"""
Circuit definition for Test 63: Component Rotation Preservation

Creates a simple circuit with 4 resistors to test rotation preservation.
Initial circuit has all resistors at default rotation (0°).
"""

from circuit_synth import circuit, Component


@circuit(name="rotated_components")
def rotated_components():
    """Circuit with 4 resistors for rotation testing."""
    # Add 4 resistors with different values
    # All start at default rotation (0° - horizontal)
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


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = rotated_components()

    circuit_obj.generate_kicad_project(
        project_name="rotated_components",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ 4 resistors circuit generated successfully!")
    print("📁 Open in KiCad: rotated_components/rotated_components.kicad_pro")
    print(f"   - 4 resistors created (R1, R2, R3, R4)")
    print(f"   - All at default rotation (0°)")
    print(f"\nNext steps:")
    print(f"   1. Manually rotate components in KiCad")
    print(f"   2. Run test to verify rotation preservation")
