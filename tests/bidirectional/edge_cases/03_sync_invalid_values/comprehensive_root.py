#!/usr/bin/env python3
"""
Test 48 - Invalid component values.

Tests behavior with edge case values: empty, whitespace, special chars.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="comprehensive_root")
def comprehensive_root():
    """Circuit with various edge case values."""

    # Empty value
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="",  # Empty
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Whitespace only
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="   ",  # Spaces
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Special characters
    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="10k@#$%",  # Special chars
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    r1[1] += vcc
    r1[2] += gnd
    r2[1] += vcc
    r2[2] += gnd
    r3[1] += vcc
    r3[2] += gnd


if __name__ == "__main__":
    circuit_obj = comprehensive_root()
    circuit_obj.generate_kicad_project(
        project_name="comprehensive_root",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    print("✅ Circuit with invalid values generated")
