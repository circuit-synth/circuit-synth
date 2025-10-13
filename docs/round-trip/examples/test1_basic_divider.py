"""
Manual Test Script - Basic Voltage Divider
Part of the Round-Trip Preservation Manual Test Plan

This is the starting point for Test 1 in MANUAL_TEST_PLAN.md
"""

from circuit_synth import Component, Net, circuit

@circuit(name="voltage_divider")
def voltage_divider():
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

    vin = Net("VIN")
    vout = Net("VOUT")
    gnd = Net("GND")

    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd

    return r1, r2

if __name__ == "__main__":
    c = voltage_divider()
    c.generate_kicad_project("voltage_divider", force_regenerate=True, generate_pcb=False)
    print("✅ Test 1: Basic voltage divider generated successfully!")
    print("📂 Open: voltage_divider/voltage_divider.kicad_sch")
