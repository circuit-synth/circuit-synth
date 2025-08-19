#!/usr/bin/env python3
"""
NeoPixel LED Driver Circuit - Reference Circuit
74AHCT125 level shifter for 5V NeoPixel control from 3.3V MCU
"""

from circuit_synth import *

@circuit(name="NeoPixel_LED_Driver")
def led_neopixel():
    """
    NeoPixel LED strip driver with level shifter
    - 74AHCT125 quad buffer for 3.3V to 5V level shifting
    - NeoPixel connector with power and data
    - Power input and filtering
    - Current limiting considerations
    """
    
    # Create power nets  
    vcc_5v = Net('VCC_5V')    # 5V for NeoPixels and level shifter
    vcc_3v3 = Net('VCC_3V3')  # 3.3V from microcontroller
    gnd = Net('GND')
    
    # Signal nets
    data_3v3 = Net('DATA_3V3')  # 3.3V data from MCU
    data_5v = Net('DATA_5V')    # 5V data to NeoPixels
    
    # 74AHCT125 level shifter (3.3V to 5V)
    level_shifter = Component(
        symbol="74xx:74AHCT125",
        ref="U",
        footprint="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm"
    )
    
    # NeoPixel connector (3-pin: 5V, GND, DATA)
    neopixel_connector = Component(
        symbol="Connector_Generic:Conn_01x03",
        ref="J", 
        footprint="Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical"
    )
    
    # Power input connector
    power_connector = Component(
        symbol="Connector_Generic:Conn_01x02",
        ref="J",
        footprint="Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"
    )
    
    # MCU interface connector
    mcu_connector = Component(
        symbol="Connector_Generic:Conn_01x03",
        ref="J", 
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
    )
    
    # Power supply filtering capacitors
    cap_bulk_5v = Component(
        symbol="Device:C_Polarized",
        ref="C",
        value="470uF",  # Large bulk cap for LED current spikes
        footprint="Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"
    )
    
    cap_bypass_5v = Component(
        symbol="Device:C", 
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    cap_bypass_3v3 = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Optional current limiting resistor (220-470 ohm)
    data_resistor = Component(
        symbol="Device:R",
        ref="R",
        value="220",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # 74AHCT125 power connections
    level_shifter["VCC"] += vcc_5v   # 5V supply
    level_shifter["GND"] += gnd      # Ground
    
    # Level shifter data path (using gate 1)
    level_shifter["1A"] += data_3v3  # Input from 3.3V MCU
    level_shifter["1Y"] += data_resistor["1"]  # Output to resistor
    level_shifter["1OE"] += gnd      # Output enable (active low)
    
    # Data signal with current limiting
    data_resistor["2"] += data_5v
    
    # NeoPixel connections
    neopixel_connector["1"] += vcc_5v    # 5V power
    neopixel_connector["2"] += gnd       # Ground
    neopixel_connector["3"] += data_5v   # Data signal
    
    # MCU interface
    mcu_connector["1"] += vcc_3v3   # 3.3V power
    mcu_connector["2"] += gnd       # Ground  
    mcu_connector["3"] += data_3v3  # Data from MCU
    
    # Power input
    power_connector["1"] += vcc_5v
    power_connector["2"] += gnd
    
    # Power supply filtering
    cap_bulk_5v["1"] += vcc_5v
    cap_bulk_5v["2"] += gnd
    cap_bypass_5v["1"] += vcc_5v
    cap_bypass_5v["2"] += gnd 
    cap_bypass_3v3["1"] += vcc_3v3
    cap_bypass_3v3["2"] += gnd
    
    # Disable unused gates to reduce power consumption
    level_shifter["2OE"] += vcc_5v   # Disable gate 2
    level_shifter["3OE"] += vcc_5v   # Disable gate 3  
    level_shifter["4OE"] += vcc_5v   # Disable gate 4
    level_shifter["2A"] += gnd       # Tie unused inputs low
    level_shifter["3A"] += gnd
    level_shifter["4A"] += gnd


if __name__ == "__main__":
    print("🚀 Generating NeoPixel LED Driver Circuit...")
    
    circuit_obj = led_neopixel()
    circuit_obj.generate_kicad_project(
        project_name="NeoPixel_LED_Driver",
        placement_algorithm="hierarchical", 
        generate_pcb=True
    )
    
    print("✅ NeoPixel LED Driver KiCad project generated!")
    print("📁 Check NeoPixel_LED_Driver/ directory for files")