#!/usr/bin/env python3
"""
Linear Regulator Power Supply for Test Case 15
Will be converted to switching regulator in KiCad
"""

from circuit_synth import Component, Net, circuit

@circuit
def power_architecture():
    """Create circuit with linear voltage regulator"""
    
    # Create nets
    vin = Net("VIN")      # 12V input
    vout = Net("5V")      # 5V output
    gnd = Net("GND")
    
    # Input connector
    j1 = Component(
        "Connector:Barrel_Jack_Switch",
        ref="J1",
        value="12V_IN",
        footprint="Connector_BarrelJack:BarrelJack_Horizontal"
    )
    j1["1"] += vin
    j1["2"] += gnd
    j1["3"] += gnd  # Switch pin to ground
    
    # Input protection diode
    d1 = Component(
        "Diode:1N4007",
        ref="D1",
        value="1N4007",
        footprint="Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal"
    )
    d1["1"] += vin      # Anode
    d1["2"] += Net("VIN_PROTECTED")  # Cathode
    
    # Linear regulator - LM7805
    u1 = Component(
        "Regulator_Linear:L7805",
        ref="U1",
        value="L7805",
        footprint="Package_TO_SOT_THT:TO-220-3_Vertical"
    )
    u1["1"] += Net("VIN_PROTECTED")  # Input
    u1["2"] += gnd                    # Ground
    u1["3"] += vout                   # Output
    
    # Input capacitor (for linear reg)
    c1 = Component(
        "Device:C",
        ref="C1",
        value="330nF",
        footprint="Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
    )
    c1["1"] += Net("VIN_PROTECTED")
    c1["2"] += gnd
    
    # Output capacitor (for linear reg)
    c2 = Component(
        "Device:C",
        ref="C2",
        value="100nF",
        footprint="Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
    )
    c2["1"] += vout
    c2["2"] += gnd
    
    # Load indicator LED
    led1 = Component(
        "Device:LED",
        ref="D2",
        value="PWR_LED",
        footprint="LED_THT:LED_D5.0mm"
    )
    r1 = Component(
        "Device:R",
        ref="R1",
        value="330",
        footprint="Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"
    )
    
    r1["1"] += vout
    r1["2"] += led1["1"]  # Anode
    led1["2"] += gnd      # Cathode
    
    # Output connector
    j2 = Component(
        "Connector:Conn_01x02_Pin",
        ref="J2",
        value="5V_OUT",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
    )
    j2["1"] += vout
    j2["2"] += gnd
    
    # Test points for measurements
    tp1 = Component(
        "Connector:TestPoint",
        ref="TP1",
        value="VIN",
        footprint="TestPoint:TestPoint_Pad_D2.0mm"
    )
    tp2 = Component(
        "Connector:TestPoint",
        ref="TP2",
        value="5V",
        footprint="TestPoint:TestPoint_Pad_D2.0mm"
    )
    
    tp1["1"] += Net("VIN_PROTECTED")
    tp2["1"] += vout

if __name__ == "__main__":
    print("Linear regulator power supply circuit generated!")
    print("\nCurrent topology:")
    print("- Linear regulator: L7805")
    print("- Input: 12V")
    print("- Output: 5V")
    print("- Efficiency: ~42%")
    print("\nWill be converted to switching regulator in KiCad:")
    print("- Replace with buck converter (e.g., LM2596)")
    print("- Add inductor (33uH)")
    print("- Add schottky diode")
    print("- Update capacitors for switching frequency")