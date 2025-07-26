#!/usr/bin/env python3
"""
Net Renaming Test Circuit for Test Case 10
Creates circuit with generic net names for renaming in KiCad
"""

from circuit_synth import Component, Net, circuit

@circuit
def net_renaming():
    """Create circuit with auto-generated net names"""
    
    # Create nets with generic names
    net1 = Net("NET1")
    net2 = Net("NET2")
    net3 = Net("NET3")
    net4 = Net("NET4")
    gnd = Net("GND")
    
    # Sensor simulation circuit
    # Voltage divider for sensor
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
    
    r1["1"] += net1  # This will become VCC
    r1["2"] += net2  # This will become SENSOR_OUT
    r2["1"] += net2
    r2["2"] += gnd
    
    # Op-amp buffer
    u1 = Component(
        "Amplifier_Operational:LM358",
        ref="U1",
        value="LM358",
        footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
    )
    
    u1["3"] += net2  # Non-inverting input (SENSOR_OUT)
    u1["2"] += net3  # Inverting input (will merge with output)
    u1["1"] += net3  # Output (BUFFER_OUT)
    u1["8"] += net1  # VCC
    u1["4"] += gnd   # GND
    
    # ADC input protection
    r3 = Component(
        "Device:R",
        ref="R3",
        value="100",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    c1 = Component(
        "Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    r3["1"] += net3  # From buffer
    r3["2"] += net4  # To ADC (will become ADC_IN)
    c1["1"] += net4
    c1["2"] += gnd
    
    # Connector for external connections
    j1 = Component(
        "Connector:Conn_01x05_Pin",
        ref="J1",
        value="Sensor_Conn",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical"
    )
    
    j1["1"] += net1  # Power
    j1["2"] += gnd   # Ground
    j1["3"] += net2  # Sensor signal
    j1["4"] += net3  # Buffered output
    j1["5"] += net4  # ADC input

if __name__ == "__main__":
    print("Net renaming test circuit generated successfully!")
    print("\nCurrent generic net names:")
    print("- NET1: Power supply")
    print("- NET2: Sensor divider output")
    print("- NET3: Buffer output")
    print("- NET4: ADC input")
    print("\nThese will be renamed in KiCad to:")
    print("- NET1 → VCC")
    print("- NET2 → SENSOR_OUT")
    print("- NET3 → BUFFER_OUT")
    print("- NET4 → ADC_IN")