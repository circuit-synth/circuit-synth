#!/usr/bin/env python3
"""
Fixture: Component with complex property types.

Tests edge cases:
- Lists
- Dicts
- Numbers (int, float)
- None values
- Empty strings
- Special characters
- Unicode
"""

from circuit_synth import circuit, Component


@circuit(name="complex_properties")
def complex_properties():
    """Circuit testing complex property types."""

    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
        # Complex types
        Tags=["precision", "low-noise", "0.1%"],  # List
        Specs={"voltage": "50V", "power": "0.125W"},  # Dict
        Cost=0.05,  # Float
        Quantity=100,  # Int
        SpecialChars="!@#$%^&*()",  # Special characters
        Unicode="µF Ω ±",  # Unicode characters
        MultiLine="Line 1\nLine 2\nLine 3",  # Newlines
        Quotes='Value with "quotes"',  # Quotes
    )


if __name__ == "__main__":
    circuit_obj = complex_properties()
    circuit_obj.generate_kicad_project(project_name="complex_properties")
    print("✅ Complex properties test generated!")
