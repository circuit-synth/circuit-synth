#!/usr/bin/env python3
"""Test that new components don't overlap existing positioned components"""
from circuit_synth import circuit, C, IC, R, LED, Net, Power, Ground


@circuit(name="voltage_regulator_led")
def voltage_regulator_led():
    """Voltage regulator circuit with LED indicator

    Initial circuit: LM7805 voltage regulator with input/output capacitors
    Then add: LED with current-limiting resistor

    Tests that added LED+resistor don't overlap with existing regulator circuit.
    """
    # Power input
    vin = Power("VIN", voltage="12V")
    gnd = Ground("GND")

    # Voltage regulator circuit (will be positioned first)
    c_in = C("C1", value="100n", footprint="C_0805_2012Metric")
    reg = IC("U1", value="LM7805", footprint="Package_TO_SOT_THT:TO-220-3_Vertical")
    c_out = C("C2", value="100n", footprint="C_0805_2012Metric")

    # Connect regulator
    Net("VIN", vin, c_in.p1, reg.pin(1))  # Input
    Net("GND", gnd, c_in.p2, reg.pin(2), c_out.p2)  # Ground
    vout = Net("VOUT", reg.pin(3), c_out.p1)  # Output

    # LED indicator circuit (will be added and should not overlap)
    r_led = R("R1", value="1k", footprint="R_0603_1608Metric")
    led = LED("D1", footprint="LED_0805_2012Metric")

    # Connect LED to output
    Net("LED+", vout, r_led.p1)
    Net("LED-", r_led.p2, led.anode)
    Net("GND", led.cathode, gnd)


if __name__ == "__main__":
    circuit_obj = voltage_regulator_led()
    circuit_obj.generate_kicad_project(project_name="voltage_regulator_led")
