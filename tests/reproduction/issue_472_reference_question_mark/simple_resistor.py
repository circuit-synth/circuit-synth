#!/usr/bin/env python3
"""
Minimal reproduction case for Issue #472: Reference designator becomes "R?" after sync.

This is the simplest possible circuit that should reproduce the bug:
- Single resistor with explicit reference "R1"
- Generate → should show R1 in KiCad
- Regenerate → BUG: shows R? instead of R1

Usage:
    python simple_resistor.py          # Generate once
    python simple_resistor.py --twice  # Generate twice (trigger bug)
"""

import sys
from circuit_synth import circuit, Component, Net


@circuit(name="simple_resistor")
def simple_resistor():
    """Minimal circuit: single resistor R1 with 4.7k value."""

    # Two resistors
    r1 = Component(
        symbol="Device:R",
        ref="R1",  # ← This should be preserved, but becomes R?
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Simple power connections
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    r1[1] += vcc
    r1[2] += gnd

    r2[1] += vcc
    r2[2] += gnd


if __name__ == "__main__":
    # Check if --twice flag is provided
    generate_twice = "--twice" in sys.argv

    circuit_obj = simple_resistor()

    print("=" * 70)
    print("🔬 Issue #472 Reproduction - Reference becomes R?")
    print("=" * 70)
    print("\n📋 Circuit: Single resistor R1 with 4.7k value")
    print()

    # First generation
    print("🔄 Generation 1...")
    circuit_obj.generate_kicad_project(
        project_name="simple_resistor",
        placement_algorithm="simple",
        generate_pcb=True,
    )
    print("✅ Generation 1 complete")
    print("   Expected in KiCad: R1 with 4.7k")
    print()

    if generate_twice:
        print("🔄 Generation 2 (reproduce bug)...")
        circuit_obj.generate_kicad_project(
            project_name="simple_resistor",
            placement_algorithm="simple",
            generate_pcb=True,
        )
        print("✅ Generation 2 complete")
        print("   🐛 BUG: Reference may now show R? instead of R1")
        print()

    print("📁 Open in KiCad: simple_resistor/simple_resistor.kicad_pro")
    print()

    if not generate_twice:
        print("💡 Run with --twice flag to reproduce bug:")
        print("   python simple_resistor.py --twice")
