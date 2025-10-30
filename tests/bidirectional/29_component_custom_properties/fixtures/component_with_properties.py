#!/usr/bin/env python3
"""
Fixture: Component with custom properties.

Tests various property types:
- Boolean: DNP=True
- String: MPN="LM358"
- Numeric string: Tolerance="1%"
- Multiple properties on one component
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
        DNP=True,  # Do Not Populate flag (boolean)
        MPN="LM358",  # Manufacturer Part Number (string)
        Tolerance="1%",  # Tolerance specification (string)
    )


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = component_with_properties()
    circuit_obj.generate_kicad_project(project_name="component_with_properties")

    print("✅ Component with properties generated successfully!")
    print("📁 Location: component_with_properties/")
    print("\nCustom properties:")
    print("  - DNP: True")
    print("  - MPN: LM358")
    print("  - Tolerance: 1%")
