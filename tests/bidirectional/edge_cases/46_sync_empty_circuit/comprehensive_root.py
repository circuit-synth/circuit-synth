#!/usr/bin/env python3
"""
Test 46 - Empty circuit edge case.

Tests that an empty circuit (no components) generates without errors.
This validates graceful handling of minimal circuits.
"""

from circuit_synth import circuit, Net


@circuit(name="comprehensive_root")
def comprehensive_root():
    """Empty root circuit - no components, only power nets."""

    # Power nets only, no components
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # No connections - just nets exist


if __name__ == "__main__":
    circuit_obj = comprehensive_root()
    circuit_obj.generate_kicad_project(
        project_name="comprehensive_root",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )

    print("✅ Empty circuit generated!")
    print("📁 Open in KiCad: comprehensive_root/comprehensive_root.kicad_pro")
    print("\nCircuit contains:")
    print("  - No components")
    print("  - Power nets: VCC, GND (not connected)")
