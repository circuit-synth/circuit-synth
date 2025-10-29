#!/usr/bin/env python3
"""
Fixture: Component without footprint assignment.

Represents a common real-world scenario:
- Component defined with symbol (Device:R)
- No footprint yet assigned (footprint="")
- Developer will add footprint later after design choices are made

Used to test graceful handling of incomplete component metadata
during iterative circuit design.
"""

from circuit_synth import circuit, Component


@circuit(name="component_no_footprint")
def component_no_footprint():
    """Circuit with a single resistor without footprint assignment.

    Tests graceful handling of missing footprint - a very common scenario
    in early design phases when footprint choices haven't been decided yet.
    """

    # Create component WITHOUT footprint (footprint="")
    # This represents the early design phase before footprint selection
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="",  # No footprint yet - will be added later
    )


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = component_no_footprint()

    circuit_obj.generate_kicad_project(project_name="component_no_footprint")

    print("✅ Component (no footprint) circuit generated successfully!")
    print("📁 Open in KiCad: component_no_footprint/component_no_footprint.kicad_pro")
    print("💡 Notice: R1 has no footprint field assigned yet")
