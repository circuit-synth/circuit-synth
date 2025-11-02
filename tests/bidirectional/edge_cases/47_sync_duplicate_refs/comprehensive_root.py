#!/usr/bin/env python3
"""
Test 47 - Duplicate component references.

Tests behavior when attempting to create duplicate component references.
Expected: Should either auto-rename or error gracefully.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="comprehensive_root")
def comprehensive_root():
    """Circuit with duplicate references - edge case test."""

    # First R1
    r1_first = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Second R1 (duplicate!)
    r1_second = Component(
        symbol="Device:R",
        ref="R1",  # Same reference as above
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Power
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # Connections
    r1_first[1] += vcc
    r1_first[2] += gnd

    r1_second[1] += vcc
    r1_second[2] += gnd


if __name__ == "__main__":
    try:
        circuit_obj = comprehensive_root()
        circuit_obj.generate_kicad_project(
            project_name="comprehensive_root",
            placement_algorithm="hierarchical",
            generate_pcb=True
        )
        print("✅ Circuit with duplicate refs generated")
        print("📁 Open in KiCad: comprehensive_root/comprehensive_root.kicad_pro")
        print("\n⚠️  Check how duplicate R1 was handled")
    except Exception as e:
        print(f"❌ Expected error: {e}")
        print("This is normal - duplicate refs should be prevented")
