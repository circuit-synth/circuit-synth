#!/usr/bin/env python3
"""
MCU Circuit Without Bypass Capacitors for Test Case 11
Intentionally missing bypass caps to be added in KiCad
"""

from circuit_synth import Component, Net, circuit

@circuit
def add_bypass_caps():
    """Create MCU circuit without bypass capacitors"""
    
    # Create power nets
    vcc_3v3 = Net("3V3")
    gnd = Net("GND")
    
    # MCU - STM32 microcontroller
    u1 = Component(
        "MCU_ST_STM32F0:STM32F030F4Px",
        ref="U1",
        value="STM32F030F4P6",
        footprint="Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm"
    )
    
    # Power connections (missing bypass caps!)
    u1["1"] += vcc_3v3   # VDD
    u1["5"] += vcc_3v3   # VDDA
    u1["16"] += gnd      # VSS
    
    # Crystal oscillator
    y1 = Component(
        "Device:Crystal",
        ref="Y1",
        value="8MHz",
        footprint="Crystal:Crystal_SMD_HC49-SD"
    )
    c1 = Component(
        "Device:C",
        ref="C1",
        value="22pF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    c2 = Component(
        "Device:C",
        ref="C2",
        value="22pF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Crystal connections
    y1["1"] += u1["2"]   # PF0-OSC_IN
    y1["2"] += u1["3"]   # PF1-OSC_OUT
    c1["1"] += u1["2"]
    c1["2"] += gnd
    c2["1"] += u1["3"]
    c2["2"] += gnd
    
    # Reset circuit
    r1 = Component(
        "Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    sw1 = Component(
        "Switch:SW_Push",
        ref="SW1",
        value="RESET",
        footprint="Button_Switch_SMD:SW_SPST_TL3342"
    )
    
    r1["1"] += vcc_3v3
    r1["2"] += u1["4"]   # NRST
    sw1["1"] += u1["4"]
    sw1["2"] += gnd
    
    # LED indicator
    led1 = Component(
        "Device:LED",
        ref="D1",
        value="GREEN",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    r2 = Component(
        "Device:R",
        ref="R2",
        value="330",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    led1["2"] += gnd     # Cathode
    led1["1"] += r2["2"]
    r2["1"] += u1["6"]   # PA0
    
    # Programming header
    j1 = Component(
        "Connector:Conn_01x04_Pin",
        ref="J1",
        value="SWD",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
    )
    
    j1["1"] += vcc_3v3   # VDD
    j1["2"] += gnd       # GND
    j1["3"] += u1["19"]  # PA13/SWDIO
    j1["4"] += u1["20"]  # PA14/SWCLK
    
    # UART header
    j2 = Component(
        "Connector:Conn_01x03_Pin",
        ref="J2",
        value="UART",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
    )
    
    j2["1"] += u1["17"]  # PA9/TX
    j2["2"] += u1["18"]  # PA10/RX
    j2["3"] += gnd

if __name__ == "__main__":
    print("MCU circuit without bypass capacitors generated!")
    print("\nMissing components to add in KiCad:")
    print("- 100nF bypass cap for VDD (pin 1)")
    print("- 100nF bypass cap for VDDA (pin 5)")
    print("- 10uF bulk capacitor for 3V3 rail")
    print("- 100nF capacitor near crystal")
    print("\nRemember: Place bypass caps as close to IC as possible!")