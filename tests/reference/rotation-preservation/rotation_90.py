#!/usr/bin/env python3
"""Reference circuit for 90° rotation testing."""

from circuit_synth import circuit, Component, Net


@circuit(name="rotation_90")
def rotation_90():
    """Single resistor for 90° rotation test - no power symbols."""

    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="330k",  # Testing 270° rotation
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Simple connection between resistors, no power
    net1 = Net("NET1")
    r1[1] += net1
    r2[1] += net1


if __name__ == "__main__":
    circuit_obj = rotation_90()
    circuit_obj.generate_kicad_project(
        project_name="rotation_90",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    print("✅ rotation_90 generated!")
