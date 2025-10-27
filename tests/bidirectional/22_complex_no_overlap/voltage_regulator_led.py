#!/usr/bin/env python3
"""Test that new components don't overlap existing positioned components"""
from circuit_synth import circuit, Component, Net


def add_large_components():
    """Add additional large components to test overlap avoidance.

    Uncomment the call to this function in the main circuit to add:
    - Large electrolytic capacitors
    - Connectors
    - Additional ICs
    - Inductors

    These should be placed without overlapping the existing regulator circuit.
    """
    # Large electrolytic capacitors (bigger footprints)
    c_bulk_in = Component(
        symbol="Device:CP",
        ref="C3",
        value="1000uF",
        footprint="Capacitor_THT:CP_Radial_D10.0mm_P5.00mm",
    )
    c_bulk_out = Component(
        symbol="Device:CP",
        ref="C4",
        value="470uF",
        footprint="Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
    )

    # Screw terminal connectors (large)
    conn_in = Component(
        symbol="Connector:Screw_Terminal_01x02",
        ref="J1",
        value="INPUT",
        footprint="TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal",
    )
    conn_out = Component(
        symbol="Connector:Screw_Terminal_01x02",
        ref="J2",
        value="OUTPUT",
        footprint="TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal",
    )

    # Additional IC (comparator)
    comparator = Component(
        symbol="Comparator:LM393",
        ref="U2",
        value="LM393",
        footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    )

    # Inductor (moderately large)
    inductor = Component(
        symbol="Device:L",
        ref="L1",
        value="100uH",
        footprint="Inductor_SMD:L_1210_3225Metric",
    )

    # Additional resistors for voltage divider
    r_div1 = Component(
        symbol="Device:R",
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0805_2012Metric",
    )
    r_div2 = Component(
        symbol="Device:R",
        ref="R3",
        value="2.2k",
        footprint="Resistor_SMD:R_0805_2012Metric",
    )

    # Connect additional components to existing nets
    vin_bulk = Net(name="VIN_BULK")
    vin_bulk += c_bulk_in[1]
    vin_bulk += conn_in[1]
    vin_bulk += inductor[1]

    gnd_bulk = Net(name="GND")
    gnd_bulk += c_bulk_in[2]
    gnd_bulk += c_bulk_out[2]
    gnd_bulk += conn_in[2]
    gnd_bulk += conn_out[2]
    gnd_bulk += comparator[4]
    gnd_bulk += r_div2[2]

    vout_bulk = Net(name="VOUT_BULK")
    vout_bulk += c_bulk_out[1]
    vout_bulk += conn_out[1]
    vout_bulk += inductor[2]
    vout_bulk += r_div1[1]

    # Voltage divider feedback
    feedback = Net(name="FEEDBACK")
    feedback += r_div1[2]
    feedback += r_div2[1]
    feedback += comparator[3]


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

    # ⚠️ UNCOMMENT THE LINE BELOW TO ADD LARGE COMPONENTS ⚠️
    # This tests that new large components don't overlap existing layout
    # add_large_components()


if __name__ == "__main__":
    circuit_obj = voltage_regulator_led()
    circuit_obj.generate_kicad_project(project_name="voltage_regulator_led")
