#!/usr/bin/env python3
"""
Test multiple power nets: GND, VCC, +3V3, +5V, -5V
"""

from circuit_synth import circuit, Component, Net


@circuit(name="multiple_power_nets")
def multiple_power_nets():
    """Circuit with multiple power nets."""
    # Create components
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r3 = Component(symbol="Device:R", ref="R3", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r4 = Component(symbol="Device:R", ref="R4", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r5 = Component(symbol="Device:R", ref="R5", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")

    # Create power nets - should all auto-detect and generate power symbols
    gnd = Net(name="GND")
    vcc = Net(name="VCC")
    v3_3 = Net(name="+3V3")
    v5 = Net(name="+5V")
    v_neg5 = Net(name="-5V")

    # Connect components to different power nets
    gnd += r1[2]
    vcc += r2[1]
    v3_3 += r3[1]
    v5 += r4[1]
    v_neg5 += r5[2]


if __name__ == "__main__":
    circuit_obj = multiple_power_nets()
    circuit_obj.generate_kicad_project(project_name="multiple_power_nets")

    print("✅ Multiple power nets generated!")
    print("📁 Open in KiCad: multiple_power_nets/multiple_power_nets.kicad_pro")
    print("")
    print("Expected power symbols:")
    print("  - GND (ground symbol)")
    print("  - VCC (+V arrow)")
    print("  - +3V3 (+V arrow)")
    print("  - +5V (+V arrow)")
    print("  - -5V (-V arrow)")
