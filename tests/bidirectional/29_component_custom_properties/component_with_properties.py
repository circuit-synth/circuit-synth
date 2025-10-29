#!/usr/bin/env python3
"""
Fixture: Component with custom properties.

Circuit with a single op-amp (LM358) that has manufacturing properties:
- DNP (Do Not Populate): true
- MPN (Manufacturer Part Number): LM358
- Tolerance: 1%

Used to test custom property preservation during generation and regeneration.
"""

from circuit_synth import circuit, Component


@circuit(name="component_with_properties")
def component_with_properties():
    """Circuit with a component having custom manufacturing properties."""

    # Create op-amp component with custom properties
    u1 = Component(
        symbol="Amplifier_Operational:LM358",
        ref="U1",
        value="LM358",
        footprint="Package_SO:SO-8_3.9x4.9mm_P1.27mm",
        # Custom properties for manufacturing
        DNP=True,                    # Do Not Populate flag
        MPN="LM358",                 # Manufacturer Part Number
        Tolerance="1%",              # Tolerance specification
    )


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = component_with_properties()

    circuit_obj.generate_kicad_project(project_name="component_with_properties")

    print("✅ Component with properties generated successfully!")
    print("📁 Open in KiCad: component_with_properties/component_with_properties.kicad_pro")
    print("\nCustom properties:")
    print("  - DNP: true")
    print("  - MPN: LM358")
    print("  - Tolerance: 1%")
