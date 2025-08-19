#!/usr/bin/env python3
"""
STM32 MCU Circuit
STM32F411 microcontroller with crystal and support circuits
"""

from circuit_synth import *

@circuit(name="STM32_MCU")
def stm32_mcu(vcc_3v3, gnd, swdio, swclk, led_control):
    """STM32F411 microcontroller subcircuit"""
    
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
    
    # Crystal load capacitors
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
    
    # Power decoupling
    cap_bulk = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    cap_bypass = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Reset components
    reset_button = Component(
        symbol="Switch:SW_Push",
        ref="SW",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3"
    )
    
    reset_pullup = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Internal reset net
    reset = Net('nRESET')
    
    # STM32 power connections
    stm32["VDD"] += vcc_3v3
    stm32["VSS"] += gnd
    stm32["VDDA"] += vcc_3v3
    stm32["VSSA"] += gnd
    
    # HSE crystal connections
    crystal[1] += stm32["PH0"]  # HSE_IN
    crystal[2] += stm32["PH1"]  # HSE_OUT
    
    # Crystal load capacitors
    cap_c1[1] += stm32["PH0"]
    cap_c1[2] += gnd
    cap_c2[1] += stm32["PH1"]
    cap_c2[2] += gnd
    
    # SWD debug connections
    stm32["PA13"] += swdio
    stm32["PA14"] += swclk
    
    # LED control
    stm32["PA5"] += led_control  # GPIO for LED
    
    # Reset circuit
    reset_pullup[1] += vcc_3v3
    reset_pullup[2] += reset
    reset_button[1] += reset
    reset_button[2] += gnd
    stm32["NRST"] += reset
    
    # Power decoupling
    cap_bulk[1] += vcc_3v3
    cap_bulk[2] += gnd
    cap_bypass[1] += vcc_3v3
    cap_bypass[2] += gnd
