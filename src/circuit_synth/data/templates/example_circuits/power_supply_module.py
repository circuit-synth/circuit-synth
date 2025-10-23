"""Power Supply Module - Dual Rail 5V/3.3V Power Supply

This example demonstrates:
- Multiple voltage regulators in one circuit
- Dual-rail power supply design
- Independent voltage regulation
- Power indicator LEDs

This circuit provides both 5V and 3.3V regulated outputs from a higher input voltage.
Useful for projects that need both voltage rails (e.g., 5V for peripherals, 3.3V for MCU).
"""
from circuit_synth import Component, Net, circuit


@circuit(name="Power_Supply_Module")
def power_supply_module():
    """Dual-rail power supply with 5V and 3.3V outputs

    This circuit provides:
    - 5V regulated output (AMS1117-5.0)
    - 3.3V regulated output (AMS1117-3.3)
    - Power indicator LEDs for each rail
    - Proper decoupling capacitors

    Input voltage range: 6.5V - 12V (limited by AMS1117 max input)
    Output currents: Up to 1A per rail
    """

    # 5V voltage regulator
    vreg_5v = Component(
        symbol="Regulator_Linear:AMS1117-5.0",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )

    # 3.3V voltage regulator
    vreg_3v3 = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )

    # Input decoupling capacitors
    cap_in_5v = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    cap_in_3v3 = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # Output decoupling capacitors
    cap_out_5v = Component(
        symbol="Device:C",
        ref="C",
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    cap_out_3v3 = Component(
        symbol="Device:C",
        ref="C",
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # Power indicator LEDs
    led_5v = Component(
        symbol="Device:LED",
        ref="D",
        value="Green",
        footprint="LED_SMD:LED_0603_1608Metric"
    )

    led_3v3 = Component(
        symbol="Device:LED",
        ref="D",
        value="Green",
        footprint="LED_SMD:LED_0603_1608Metric"
    )

    # Current limiting resistors for LEDs
    r_led_5v = Component(
        symbol="Device:R",
        ref="R",
        value="330",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r_led_3v3 = Component(
        symbol="Device:R",
        ref="R",
        value="330",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Define power nets
    vin = Net('VIN')           # Input voltage (6.5V-12V)
    vout_5v = Net('VOUT_5V')   # 5V regulated output
    vout_3v3 = Net('VOUT_3V3') # 3.3V regulated output
    gnd = Net('GND')           # Ground

    # Connect 5V regulator
    vreg_5v["VIN"] += vin
    vreg_5v["VOUT"] += vout_5v
    vreg_5v["GND"] += gnd

    # Connect 3.3V regulator
    vreg_3v3["VIN"] += vin
    vreg_3v3["VOUT"] += vout_3v3
    vreg_3v3["GND"] += gnd

    # Connect input capacitors
    cap_in_5v[1] += vin
    cap_in_5v[2] += gnd

    cap_in_3v3[1] += vin
    cap_in_3v3[2] += gnd

    # Connect output capacitors
    cap_out_5v[1] += vout_5v
    cap_out_5v[2] += gnd

    cap_out_3v3[1] += vout_3v3
    cap_out_3v3[2] += gnd

    # Connect 5V power indicator LED
    r_led_5v[1] += vout_5v
    r_led_5v[2] += Net('LED_5V_ANODE')
    led_5v["A"] += Net('LED_5V_ANODE')
    led_5v["K"] += gnd

    # Connect 3.3V power indicator LED
    r_led_3v3[1] += vout_3v3
    r_led_3v3[2] += Net('LED_3V3_ANODE')
    led_3v3["A"] += Net('LED_3V3_ANODE')
    led_3v3["K"] += gnd


if __name__ == '__main__':
    # Generate KiCad project
    circuit_obj = power_supply_module()

    circuit_obj.generate_kicad_project(
        project_name="power_supply_module",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )

    print("✅ Dual-rail power supply circuit generated!")
    print("📁 Open in KiCad: power_supply_module/power_supply_module.kicad_pro")
    print()
    print("📊 Circuit Specifications:")
    print("   Input:  6.5V - 12V")
    print("   Output 1: 5.0V @ 1A max")
    print("   Output 2: 3.3V @ 1A max")
    print()
    print("💡 Features:")
    print("   • Independent voltage regulation")
    print("   • Power indicator LEDs (green)")
    print("   • Proper decoupling capacitors")
    print()
    print("🔧 Next Steps:")
    print("   • Add input protection (reverse polarity, overvoltage)")
    print("   • Add output filtering if needed for sensitive circuits")
    print("   • Consider heatsinking for continuous 1A loads")
