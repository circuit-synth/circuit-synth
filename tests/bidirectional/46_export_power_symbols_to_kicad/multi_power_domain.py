#!/usr/bin/env python3
"""
Fixture: Multi-power-domain circuit with 5 distinct power rails.

Circuit with 5 resistors connected to different power domains:
- R1 → VCC_3V3 (3.3V logic supply)
- R2 → VCC_5V (5V peripheral supply)
- R3 → VCC_12V (12V power supply)
- R4 → GND (digital ground)
- R5 → AGND (analog ground)

Used for testing:
1. Export of multiple distinct power symbols to KiCad
2. Power symbol type selection (VCC vs GND variations)
3. Analog vs digital ground separation
4. Power symbol reuse when adding components
"""

from circuit_synth import *


@circuit(name="multi_power_domain")
def multi_power_domain():
    """Circuit demonstrating 5 distinct power domains.

    Real-world embedded system power architecture:
    - 3.3V logic (microcontroller)
    - 5V peripherals (USB, sensors)
    - 12V power (motors, actuators)
    - Digital ground (logic reference)
    - Analog ground (ADC/DAC reference)
    """

    # Create five resistors
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
    r5 = Component(
        symbol="Device:R",
        ref="R5",
        value="100",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Create five independent power domain nets
    # Each represents a separate voltage rail in the system

    # 3.3V logic supply - microcontroller power
    net_3v3 = Net(name="VCC_3V3")
    net_3v3 += r1[1]  # R1 pin 1 to 3.3V

    # 5V peripheral supply - USB, sensors
    net_5v = Net(name="VCC_5V")
    net_5v += r2[1]  # R2 pin 1 to 5V

    # 12V power supply - motors, high power loads
    net_12v = Net(name="VCC_12V")
    net_12v += r3[1]  # R3 pin 1 to 12V

    # Digital ground - logic reference
    net_gnd = Net(name="GND")
    net_gnd += r4[1]  # R4 pin 1 to GND

    # Analog ground - ADC/DAC reference (separate from digital)
    net_agnd = Net(name="AGND")
    net_agnd += r5[1]  # R5 pin 1 to AGND

    # Note: For step 4 of test, we'll add R6 using VCC_3V3
    # This tests power symbol reuse
    # Uncomment below to add R6:
    # r6 = Component(
    #     symbol="Device:R",
    #     ref="R6",
    #     value="22k",
    #     footprint="Resistor_SMD:R_0603_1608Metric",
    # )
    # net_3v3 += r6[1]  # R6 shares VCC_3V3 with R1


if __name__ == "__main__":
    circuit_obj = multi_power_domain()
    circuit_obj.generate_kicad_project(
        project_name="multi_power_domain",
        placement_algorithm="simple",
        generate_pcb=False
    )
    print("✅ Multi-power-domain circuit generated!")
    print("📁 Open in KiCad: multi_power_domain/multi_power_domain.kicad_pro")
    print("\n📊 Power domains:")
    print("   - R1 → VCC_3V3 (3.3V logic)")
    print("   - R2 → VCC_5V (5V peripherals)")
    print("   - R3 → VCC_12V (12V power)")
    print("   - R4 → GND (digital ground)")
    print("   - R5 → AGND (analog ground)")
