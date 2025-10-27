#!/usr/bin/env python3
"""
Demo script to test component deletion with preserve_user_components=False

Usage:
1. Run this script as-is to create a circuit with R1 and R2
2. Comment out R2 in the code
3. Run again - R2 will be removed from KiCad schematic
"""

from circuit_synth import *


@circuit(name="deletion_test")
def deletion_test():
    """Test circuit for component deletion"""

    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )


if __name__ == "__main__":
    circuit = deletion_test()

    # IMPORTANT: preserve_user_components=False enables component deletion
    # When False, components deleted from Python will be removed from KiCad
    circuit.generate_kicad_project(
        "deletion_test",
        preserve_user_components=False  # Enable deletion
    )

    print("\n✅ Circuit generated")
    print("\nTo test deletion:")
    print("1. Check deletion_test/deletion_test.kicad_sch - should have R1 and R2")
    print("2. Comment out R2 in this file")
    print("3. Run this script again")
    print("4. Check the schematic - R2 should be removed!")
