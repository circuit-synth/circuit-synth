#!/usr/bin/env python3
"""
Circuit designed for BOM export testing.

Components:
- 10x 10k resistors (R1-R10) - Should group in BOM with Qty=10
- 2x 100nF capacitors (C1-C2) - Should group in BOM with Qty=2
- 1x LED (D1) marked DNP - Should be excluded from BOM by default
- 1x 1k resistor (R11) marked DNP - Should be excluded from BOM by default
- 1x 10k resistor (R12) - COMMENTED OUT initially, uncomment for modification test

Real-world scenario:
Pull-up resistor network with bypass capacitors, status LED, and current limiting resistor.
DNP components for prototype testing.
"""
from circuit_synth import Circuit, Component


def main():
    circuit = Circuit("circuit_for_bom")

    # 10x 10k resistors - should group in BOM
    # Positioned in 2x5 grid pattern
    x_offset = 0
    for i in range(1, 11):
        col = (i - 1) // 5
        row = (i - 1) % 5
        x = 50 + col * 30
        y = 40 + row * 20

        r = Component(
            symbol="Device:R",
            ref=f"R{i}",
            value="10k",
            footprint="Resistor_SMD:R_0603_1608Metric",
        )
        circuit.add_component(r)

    # 2x 100nF capacitors - should group in BOM
    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    circuit.add_component(c1)

    c2 = Component(
        symbol="Device:C",
        ref="C2",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )
    circuit.add_component(c2)

    # LED marked DNP - should be excluded from BOM by default
    d1 = Component(
        symbol="Device:LED",
        ref="D1",
        value="LED",
        footprint="LED_SMD:LED_0603_1608Metric",
        dnp=True,  # Mark as Do Not Populate (lowercase 'dnp' for KiCad)
    )
    circuit.add_component(d1)

    # 1k resistor marked DNP - should be excluded from BOM by default
    r11 = Component(
        symbol="Device:R",
        ref="R11",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
        dnp=True,  # Mark as Do Not Populate (lowercase 'dnp' for KiCad)
    )
    circuit.add_component(r11)

    # R12 - COMMENTED OUT for initial test
    # Uncomment this for modification test (should add to 10k resistor group)
    # r12 = Component(
    #     symbol="Device:R",
    #     ref="R12",
    #     value="10k",
    #     footprint="Resistor_SMD:R_0603_1608Metric",
    # )
    # circuit.add_component(r12)

    # Generate KiCad project
    circuit.generate_kicad_project(project_name=circuit.name)
    print(f"Generated circuit: {circuit.name}")
    print(f"Components: R1-R10 (10k), C1-C2 (100nF), D1 (LED, DNP), R11 (1k, DNP)")
    print(f"Ready for BOM export")


if __name__ == "__main__":
    main()
