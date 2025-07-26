#!/usr/bin/env python3
"""
Hierarchical Circuit for Test Case 04
Main sheet with power supply and sub-sheet with voltage divider
"""

from circuit_synth import Component, Net, circuit

@circuit(name="voltage_divider")
def voltage_divider():
    """Create a voltage divider sub-circuit"""
    
    # Create internal nets
    vin = Net("VIN")
    vout = Net("VOUT")
    gnd = Net("GND")
    
    # Create voltage divider components
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
    
    # Connect components
    r1["1"] += vin
    r1["2"] += vout
    r2["1"] += vout
    r2["2"] += gnd

@circuit
def hierarchical_design():
    """Create main circuit with hierarchical sheet"""
    
    # Create main sheet nets
    vcc = Net("VCC")
    gnd = Net("GND")
    divided_voltage = Net("DIVIDED_VOLTAGE")
    
    # Add power supply components
    c1 = Component(
        "Device:C",
        ref="C1",
        value="100uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    c1["1"] += vcc
    c1["2"] += gnd
    
    # Instantiate voltage divider
    vdiv = voltage_divider()
    vdiv.VIN += vcc
    vdiv.VOUT += divided_voltage
    vdiv.GND += gnd
    
    # Add output connector
    j1 = Component(
        "Connector:Conn_01x03_Pin",
        ref="J1",
        value="Output",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
    )
    j1["1"] += vcc
    j1["2"] += divided_voltage
    j1["3"] += gnd

if __name__ == "__main__":
    print("Hierarchical circuit for Test 04 generated successfully!")
    print("Main sheet: Power supply capacitor and output connector")
    print("Sub-sheet: Voltage divider (R1, R2)")