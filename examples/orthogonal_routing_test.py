#!/usr/bin/env python3
"""
Simple test circuit for orthogonal routing functionality.

This example demonstrates the basic orthogonal routing feature with
automatic blind/buried via support.
"""

from circuit_synth import Component, Net, circuit


@circuit
def orthogonal_test(circuit):
    """
    Simple test circuit with a few components to verify orthogonal routing works.

    Tests:
    - Basic orthogonal routing parameter
    - Custom via size specification
    - DSN export with orthogonal layer directions
    """
    # Create some simple components
    r1 = Component(
        "Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r2 = Component(
        "Device:R",
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r3 = Component(
        "Device:R",
        ref="R3",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    c1 = Component(
        "Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Create a simple voltage divider network
    vcc = Net("VCC")
    mid = Net("MID")
    gnd = Net("GND")

    # Connect components
    vcc += r1[1]
    r1[2] += mid
    mid += r2[1], c1[1]
    r2[2] += gnd
    c1[2] += gnd
    r3[1] += mid
    r3[2] += gnd


if __name__ == "__main__":
    import sys

    # Create the circuit
    test_circuit = orthogonal_test()

    # Generate with orthogonal routing
    print("\n" + "=" * 80)
    print("ORTHOGONAL ROUTING TEST")
    print("=" * 80)
    print("\nGenerating KiCad project with orthogonal routing...")
    print("- Routing style: orthogonal (90° only)")
    print("- Via size: 0.6/0.3 (0.6mm drill, 0.3mm annular ring)")
    print("- Blind/buried vias: enabled automatically")
    print()

    try:
        test_circuit.generate_kicad_project(
            "orthogonal_routing_test",
            routing_style="orthogonal",  # Enable orthogonal routing
            via_size="0.6/0.3",          # Specify via size (or omit for same default)
            generate_pcb=True,
            placement_algorithm="connection_centric"
        )

        print("\n" + "=" * 80)
        print("✓ SUCCESS - Project generated!")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Open KiCad and load 'orthogonal_routing_test.kicad_pro'")
        print("2. Open the PCB editor")
        print("3. Use Freerouting to auto-route (if auto_route wasn't enabled)")
        print("4. Verify all routes are orthogonal (90° angles only)")
        print("5. Check that via sizes match 0.6/0.3 specification")
        print()

    except Exception as e:
        print("\n" + "=" * 80)
        print("✗ FAILED - Error during generation")
        print("=" * 80)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
