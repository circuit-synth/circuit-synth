#!/usr/bin/env python3
"""
Fixture: Two resistors connected via SIGNAL net for wire routing preservation test.

This circuit is used to test whether custom wire routing paths (with corners,
multiple segments) are preserved during bidirectional sync.

Workflow:
1. Generate KiCad with straight-line wire (default)
2. Manually route wire with L-shaped path in KiCad
3. Modify component value in Python
4. Regenerate → Check if routing preserved or reset
"""

from circuit_synth import circuit, Component, Net


@circuit(name="routed_circuit")
def routed_circuit():
    """Circuit with two resistors connected via SIGNAL net.

    Used for testing wire routing preservation during bidirectional sync.
    """
    # R1: 10k resistor (will be modified to 22k in test)
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # R2: 4.7k resistor (unchanged during test)
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Connect R1 pin 2 to R2 pin 1 via SIGNAL net
    # This net will have custom routing added manually in KiCad
    signal_net = Net(name="SIGNAL")
    signal_net += r1[2]
    signal_net += r2[1]


if __name__ == "__main__":
    circuit_obj = routed_circuit()
    circuit_obj.generate_kicad_project(project_name="routed_circuit")
    print("✅ Routed circuit generated!")
    print("📁 Open in KiCad: routed_circuit/routed_circuit.kicad_pro")
    print("\n📝 Next steps:")
    print("   1. Open schematic in KiCad")
    print("   2. Manually route wire with L-shaped path (add corners)")
    print("   3. Save schematic")
    print("   4. Modify R1 value in Python and regenerate")
    print("   5. Check if wire routing is preserved")
