"""
Circuit fixture generators for automated testing.

These functions create circuit-synth Circuit objects for testing.
They mirror the manual test circuits in tests/bidirectional/.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="blank")
def blank():
    """Blank circuit with no components."""
    pass


@circuit(name="single_resistor")
def single_resistor():
    """Circuit with a single 10kΩ resistor."""
    Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )


@circuit(name="two_resistors")
def two_resistors():
    """Circuit with two resistors."""
    Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )


@circuit(name="two_resistors_connected")
def two_resistors_connected():
    """Circuit with two resistors connected via NET1."""
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

    # Connect R1 pin 1 to R2 pin 1 via NET1
    net1 = Net(name="NET1")
    net1 += r1[1]
    net1 += r2[1]


@circuit(name="three_resistors_on_net")
def three_resistors_on_net():
    """Circuit with three resistors on a single net."""
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
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    net1 = Net(name="NET1")
    net1 += r1[1]
    net1 += r2[1]
    net1 += r3[1]


@circuit(name="four_resistors_two_nets")
def four_resistors_two_nets():
    """Circuit with four resistors on two separate nets."""
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
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )
    r4 = Component(
        symbol="Device:R",
        ref="R4",
        value="2.2k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    net1 = Net(name="NET1")
    net1 += r1[1]
    net1 += r2[1]

    net2 = Net(name="NET2")
    net2 += r3[1]
    net2 += r4[1]


@circuit(name="voltage_regulator_led")
def voltage_regulator_led():
    """Voltage regulator circuit with LED indicator."""
    # Voltage regulator circuit
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

    # LED indicator circuit
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
