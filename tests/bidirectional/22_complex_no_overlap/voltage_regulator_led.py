#!/usr/bin/env python3
"""Test that new components don't overlap existing positioned components"""
from circuit_synth import circuit, Component, Net


@circuit(name="voltage_regulator_led")
def voltage_regulator_led():
    """Voltage regulator circuit with LED indicator

    Initial circuit: LM7805 voltage regulator with input/output capacitors
    Then add: LED with current-limiting resistor

    Tests that added LED+resistor don't overlap with existing regulator circuit.
    """
    # Voltage regulator circuit (will be positioned first)
    c_in = Component(
        symbol="Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )
    reg = Component(
        symbol="Regulator_Linear:LM7805_TO220",
        ref="U1",
        value="LM7805",
        footprint="Package_TO_SOT_THT:TO-220-3_Vertical",
    )
    c_out = Component(
        symbol="Device:C",
        ref="C2",
        value="100nF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )

    # LED indicator circuit (will be added and should not overlap)
    r_led = Component(
        symbol="Device:R",
        ref="R1",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    led = Component(
        symbol="Device:LED",
        ref="D1",
        value="LED",
        footprint="LED_SMD:LED_0805_2012Metric",
    )

    # Connect regulator
    vin = Net(name="VIN")
    vin += c_in[1]
    vin += reg[1]  # Input pin

    gnd = Net(name="GND")
    gnd += c_in[2]
    gnd += reg[2]  # Ground pin
    gnd += c_out[2]
    gnd += led[2]  # LED cathode

    vout = Net(name="VOUT")
    vout += reg[3]  # Output pin
    vout += c_out[1]
    vout += r_led[1]

    # LED connection
    led_net = Net(name="LED")
    led_net += r_led[2]
    led_net += led[1]  # LED anode


if __name__ == "__main__":
    circuit_obj = voltage_regulator_led()
    circuit_obj.generate_kicad_project(project_name="voltage_regulator_led")
