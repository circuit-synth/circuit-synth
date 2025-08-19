#!/usr/bin/env python3
"""
STM32 Basic Development Board - Reference Circuit
STM32F411 microcontroller with crystal, debug header, and power supply
"""

from circuit_synth import *

@circuit(name="STM32_Basic_Board")
def stm32_basic(VCC_3V3, GND, SWDIO, SWCLK):
    """
    Basic STM32F411 development board
    - STM32F411CEUx microcontroller (LQFP-48)
    - 8MHz HSE crystal oscillator  
    - SWD debug header
    - Power supply with decoupling
    - Reset button
    """
    
    # Internal reset net
    reset = Net('nRESET')
    
    # STM32F411 microcontroller
    stm32 = Component(
        symbol="MCU_ST_STM32F4:STM32F411CEUx",
        ref="U",
        footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
    )
    
    # 8MHz HSE crystal
    crystal = Component(
        symbol="Device:Crystal",
        ref="Y", 
        value="8MHz",
        footprint="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm"
    )
    
    # Crystal load capacitors (18pF typical for 8MHz)
    cap_c1 = Component(
        symbol="Device:C",
        ref="C",
        value="18pF",
        footprint="Capacitor_SMD:C_0603_1608Metric" 
    )
    
    cap_c2 = Component(
        symbol="Device:C",
        ref="C",
        value="18pF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Power supply decoupling capacitors
    cap_bulk = Component(
        symbol="Device:C",
        ref="C", 
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    cap_bypass1 = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    cap_bypass2 = Component(
        symbol="Device:C",
        ref="C",
        value="100nF", 
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # SWD debug header  
    debug_header = Component(
        symbol="Connector_Generic:Conn_01x04",
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
    )
    
    # Reset button
    reset_button = Component(
        symbol="Switch:SW_Push", 
        ref="SW",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3"
    )
    
    # Reset pull-up resistor
    reset_pullup = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    
    # STM32 power connections  
    stm32["VDD"] += VCC_3V3
    stm32["VSS"] += GND
    stm32["VDDA"] += VCC_3V3  # Analog power
    stm32["VSSA"] += GND      # Analog ground
    
    # HSE crystal connections
    crystal["1"] += stm32["PH0"]  # HSE_IN
    crystal["2"] += stm32["PH1"]  # HSE_OUT
    
    # Crystal load capacitors
    cap_c1["1"] += stm32["PH0"]
    cap_c1["2"] += GND
    cap_c2["1"] += stm32["PH1"] 
    cap_c2["2"] += GND
    
    # SWD debug connections
    debug_header["1"] += VCC_3V3         # Power
    debug_header["2"] += GND             # Ground  
    debug_header["3"] += SWDIO           # SWDIO
    debug_header["4"] += SWCLK           # SWCLK
    stm32["PA13"] += SWDIO   # Connect to MCU
    stm32["PA14"] += SWCLK   # Connect to MCU
    
    # Reset circuit
    reset_pullup["1"] += VCC_3V3
    reset_pullup["2"] += reset
    reset_button["1"] += reset
    reset_button["2"] += GND
    stm32["NRST"] += reset
    
    # Power supply decoupling
    cap_bulk["1"] += VCC_3V3
    cap_bulk["2"] += GND
    cap_bypass1["1"] += VCC_3V3 
    cap_bypass1["2"] += GND
    cap_bypass2["1"] += VCC_3V3
    cap_bypass2["2"] += GND


if __name__ == "__main__":
    # Create nets for standalone testing
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    swdio = Net('SWDIO') 
    swclk = Net('SWCLK')
    
    circuit_obj = stm32_basic(vcc_3v3, gnd, swdio, swclk)
    circuit_obj.generate_kicad_project(project_name="STM32_Basic_Board")