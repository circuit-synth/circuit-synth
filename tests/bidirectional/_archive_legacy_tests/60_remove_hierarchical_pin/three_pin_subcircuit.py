#!/usr/bin/env python3
"""
Hierarchical circuit with 3-pin subcircuit interface.

Initial state:
- Subcircuit has VCC, GND, SIGNAL hierarchical pins
- Resistor inside subcircuit connected to VCC, GND
- SIGNAL present as hierarchical interface (unused)
- Clean interface for testing pin removal
"""

from circuit_synth import Component, Net, circuit


@circuit(name="PowerAndSignal")
def power_and_signal_subcircuit(VCC, GND, SIGNAL):
    """
    Subcircuit with resistor connected to power pins.
    SIGNAL pin exists but is not connected to internal components.
    """
    # Component in subcircuit - resistor connected to power
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Connect resistor to hierarchical power pins
    r1[1] += VCC  # One end to VCC (hierarchical label)
    r1[2] += GND  # Other end to GND (hierarchical label)

    # SIGNAL is passed as parameter but not connected to R1
    # This represents a signal passing through the subcircuit interface


@circuit(name="ThreePinSubcircuit")
def main():
    """
    Top-level circuit demonstrating 3 hierarchical pins.
    The SIGNAL pin will be removed during testing.
    """
    # Create power and signal nets in parent
    vcc = Net("VCC")
    gnd = Net("GND")
    signal = Net("SIGNAL")

    # Create subcircuit with all 3 hierarchical connections
    power_and_signal_subcircuit(vcc, gnd, signal)

    print(f"✅ Circuit created successfully!")
    print(f"   Hierarchical ports: VCC, GND, SIGNAL")
    print(f"   Component in subcircuit: R1 (resistor)")
    print(f"   Note: SIGNAL port exists but is not connected to components")
    print(f"\n   Ready for test: Will remove SIGNAL and verify cleanup")


if __name__ == "__main__":
    c = main()
    print(f"\nGenerating KiCad project: {c.name}")
    c.generate_kicad_project("three_pin_subcircuit", force_regenerate=True)
    print(f"\n✅ Project generated successfully!")
    print(f"   Expected hierarchical structure:")
    print(f"   - Parent: ThreePinSubcircuit.kicad_sch (with sheet symbol)")
    print(f"   - Subcircuit: PowerAndSignal.kicad_sch (with hierarchical labels)")
    print(f"   - Sheet symbol should have pins: VCC, GND, SIGNAL")
    print(f"   - Subcircuit should have hierarchical labels: VCC, GND, SIGNAL")
