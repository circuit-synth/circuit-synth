#!/usr/bin/env python3
"""Test circuit for manual position preservation.

This circuit has a single resistor. We'll test that manual position
changes in KiCad are preserved when regenerating from Python.
"""

from circuit_synth import *


@circuit(name="position_test")
def position_test_circuit():
    """Single resistor for testing position preservation."""
    r = Component(
        symbol="Device:R", ref="R1", value="10k", footprint="R_0603_1608Metric"
    )

    # r = Component(
    #     symbol="Device:R", ref="R2", value="10k", footprint="R_0603_1608Metric"
    # )


if __name__ == "__main__":
    circuit = position_test_circuit()
    circuit.generate_kicad_project("position_test")
    print("✅ Circuit generated at: position_test/position_test.kicad_sch")
    print("\nNext steps:")
    print("1. Open position_test/position_test.kicad_sch in KiCad")
    print("2. Move R1 to a new position")
    print("3. Save and close KiCad")
    print("4. Run this script again")
    print("5. Open the schematic - R1 should be at your new position!")
