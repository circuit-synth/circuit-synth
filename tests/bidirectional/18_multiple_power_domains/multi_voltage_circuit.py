#!/usr/bin/env python3
"""
Fixture: Multi-voltage circuit with 4 resistors on different power domains.

Starting point for testing multiple power rails (VCC, 3V3, 5V, GND).
Each resistor connects to a different power domain.

Used for:
1. Testing multi-voltage circuit support
2. Validating power domain assignments
3. Testing iterative power domain modifications
"""

from circuit_synth import *


@circuit(name="multi_voltage_circuit")
def multi_voltage_circuit():
    """Circuit with 4 resistors on different power domains.

    Each resistor connects to a different voltage rail:
    - R1 → VCC (12V primary power)
    - R2 → 3V3 (3.3V logic supply)
    - R3 → 5V (5V supply)
    - R4 → GND (ground reference)
    """

    # Create four resistors
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
    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="2.2k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r4 = Component(
        symbol="Device:R",
        ref="R4",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Create four independent power domain nets
    # Each net represents a separate voltage rail

    # VCC net (12V primary power) - R1 connects here
    net_vcc = Net(name="VCC")
    net_vcc += r1[1]  # R1 pin 1 to VCC

    # 3V3 net (3.3V logic supply) - R2 connects here
    net_3v3 = Net(name="3V3")
    net_3v3 += r2[1]  # R2 pin 1 to 3V3

    # 5V net (5V supply) - R3 connects here
    net_5v = Net(name="5V")
    net_5v += r3[1]  # R3 pin 1 to 5V

    # GND net (ground reference) - R4 connects here
    net_gnd = Net(name="GND")
    net_gnd += r4[1]  # R4 pin 1 to GND

    # Note: R2 and R3 can be swapped to test power domain modifications
    # To modify: remove r2[1] from net_3v3 and add to net_5v


if __name__ == "__main__":
    circuit_obj = multi_voltage_circuit()
    circuit_obj.generate_kicad_project(
        project_name="multi_voltage_circuit",
        placement_algorithm="simple",
        generate_pcb=True
    )
    print("✅ Multi-voltage circuit generated!")
    print("📁 Open in KiCad: multi_voltage_circuit/multi_voltage_circuit.kicad_pro")
    print("\n📊 Power domains:")
    print("   - R1 → VCC (12V)")
    print("   - R2 → 3V3 (3.3V)")
    print("   - R3 → 5V (5V)")
    print("   - R4 → GND (0V)")
