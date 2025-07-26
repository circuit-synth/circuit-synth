#!/usr/bin/env python3
"""
Functional Circuit Without Test Points for Test Case 13
Missing debug/test infrastructure to be added in KiCad
"""

from circuit_synth import Component, Net, circuit

@circuit
def add_test_points():
    """Create a sensor interface circuit without test points"""
    
    # Create nets
    vcc_5v = Net("5V")
    vcc_3v3 = Net("3V3")
    gnd = Net("GND")
    sensor_raw = Net("SENSOR_RAW")
    sensor_filtered = Net("SENSOR_FILTERED")
    adc_input = Net("ADC_INPUT")
    i2c_sda = Net("I2C_SDA")
    i2c_scl = Net("I2C_SCL")
    
    # 5V to 3.3V regulator
    u1 = Component(
        "Regulator_Linear:AMS1117-3.3",
        ref="U1",
        value="AMS1117-3.3",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    u1["1"] += gnd
    u1["2"] += vcc_3v3
    u1["3"] += vcc_5v
    
    # Input and output caps for regulator
    c1 = Component(
        "Device:C",
        ref="C1",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    c2 = Component(
        "Device:C",
        ref="C2",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    c1["1"] += vcc_5v
    c1["2"] += gnd
    c2["1"] += vcc_3v3
    c2["2"] += gnd
    
    # Analog sensor with amplification
    # Sensor connector (missing test points on signals!)
    j1 = Component(
        "Connector:Conn_01x03_Pin",
        ref="J1",
        value="SENSOR",
        footprint="Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical"
    )
    j1["1"] += vcc_5v
    j1["2"] += sensor_raw
    j1["3"] += gnd
    
    # Op-amp for signal conditioning
    u2 = Component(
        "Amplifier_Operational:MCP6001",
        ref="U2",
        value="MCP6001",
        footprint="Package_TO_SOT_SMD:SOT-23-5"
    )
    u2["1"] += sensor_filtered  # Output
    u2["2"] += gnd             # V-
    u2["3"] += sensor_raw      # V+ input
    u2["4"] += sensor_filtered  # V- input (unity gain)
    u2["5"] += vcc_3v3         # V+
    
    # Low-pass filter
    r1 = Component(
        "Device:R",
        ref="R1",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    c3 = Component(
        "Device:C",
        ref="C3",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    r1["1"] += sensor_filtered
    r1["2"] += adc_input
    c3["1"] += adc_input
    c3["2"] += gnd
    
    # I2C temperature sensor
    u3 = Component(
        "Sensor_Temperature:TMP102",
        ref="U3",
        value="TMP102",
        footprint="Package_TO_SOT_SMD:SOT-23-6"
    )
    u3["1"] += i2c_scl
    u3["2"] += gnd
    u3["3"] += i2c_sda
    u3["4"] += vcc_3v3
    u3["5"] += gnd  # ADD0
    u3["6"] += gnd  # ALERT
    
    # I2C pull-ups
    r2 = Component(
        "Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    r3 = Component(
        "Device:R",
        ref="R3",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    r2["1"] += vcc_3v3
    r2["2"] += i2c_sda
    r3["1"] += vcc_3v3
    r3["2"] += i2c_scl
    
    # Main connector (no debug header!)
    j2 = Component(
        "Connector:Conn_01x06_Pin",
        ref="J2",
        value="MAIN",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical"
    )
    j2["1"] += vcc_5v
    j2["2"] += gnd
    j2["3"] += adc_input
    j2["4"] += i2c_sda
    j2["5"] += i2c_scl
    j2["6"] += gnd

if __name__ == "__main__":
    print("Sensor interface circuit without test points generated!")
    print("\nMissing debug features to add in KiCad:")
    print("- Test points on SENSOR_RAW signal")
    print("- Test points on SENSOR_FILTERED signal")
    print("- Test points on ADC_INPUT")
    print("- Test points on power rails (5V, 3V3)")
    print("- Debug UART connector")
    print("- I2C debug header")
    print("- Ground test points near analog section")