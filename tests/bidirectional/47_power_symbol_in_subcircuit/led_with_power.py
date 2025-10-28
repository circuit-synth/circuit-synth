#!/usr/bin/env python3
"""
Fixture: LED circuit with power symbols IN subcircuit (not root).

This tests power distribution through hierarchical circuits:
- Root sheet: Establishes VCC power rail
- Child sheet (LED_Circuit): Contains LED and power symbols

This is a CRITICAL real-world pattern: power nets originate on root
but are distributed to child sheets where components connect via local
power symbols and hierarchical labels.

Starting point:
- One LED (D1) with VCC/GND power symbols in child sheet
- Power symbols commented out initially for test validation

Test will add second LED (D2) to verify power symbol reuse.
"""

from circuit_synth import *


@circuit(name="led_with_power")
def led_with_power():
    """Hierarchical LED circuit with power distribution to child sheet.

    Root sheet:
    - Establishes VCC power net (global power rail)

    Child sheet (LED_Circuit):
    - LED component (D1) requiring VCC and GND
    - Power symbols (VCC, GND) placed IN child sheet
    - Current limiting resistor (R1)
    - Hierarchical labels connecting to parent
    """
    from circuit_synth.core.decorators import get_current_circuit

    root = get_current_circuit()

    # Root sheet: Establish VCC power rail
    # In real designs, this would connect to power supply/regulator
    vcc = Net(name="VCC")

    # START_MARKER: Test will modify between these markers to add subcircuit

    # Child sheet: LED circuit with power symbols
    led_circuit = Circuit("LED_Circuit")

    # Components on child sheet
    d1 = Component(
        symbol="Device:LED",
        ref="D1",
        value="Red",
        footprint="LED_SMD:LED_0603_1608Metric",
    )

    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="330",  # 330 ohm current limiting resistor
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    led_circuit.add_component(d1)
    led_circuit.add_component(r1)

    # Note: Power symbols initially commented out for test validation
    # Test will uncomment to verify power symbol generation in child sheet
    # vcc_child = Net(name="VCC")
    # gnd_child = Net(name="GND")
    # vcc_child += r1[1]  # Resistor to VCC
    # r1[2] += d1["A"]  # Resistor to LED anode
    # d1["K"] += gnd_child  # LED cathode to GND

    root.add_subcircuit(led_circuit)

    # END_MARKER


if __name__ == "__main__":
    circuit_obj = led_with_power()
    circuit_obj.generate_kicad_project(
        project_name="led_with_power", placement_algorithm="simple", generate_pcb=True
    )
    print("✅ LED with power fixture generated!")
    print("📁 Open in KiCad: led_with_power/led_with_power.kicad_pro")
