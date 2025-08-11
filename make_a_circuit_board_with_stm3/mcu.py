from circuit_synth import *

@circuit(name="mcu_circuit")
def mcu_circuit(vcc_3v3, gnd):
    """STM32 microcontroller circuit"""
    
    # STM32 MCU
    mcu = Component(
        symbol="MCU_ST_STM32F4:STM32F407VETx",
        ref="U2",
        footprint="Package_LQFP:LQFP-100_14x14mm_P0.5mm"
    )
    
    # Decoupling capacitors
    cap1 = Component(
        symbol="Device:C",
        ref="C3",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    cap2 = Component(
        symbol="Device:C",
        ref="C4", 
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Crystal oscillator
    crystal = Component(
        symbol="Device:Crystal",
        ref="Y1",
        footprint="Crystal:Crystal_SMD_HC49-SD"
    )
    
    # Crystal load capacitors
    cap_xtal1 = Component(
        symbol="Device:C",
        ref="C5",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    cap_xtal2 = Component(
        symbol="Device:C", 
        ref="C6",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Power connections
    mcu[100] += vcc_3v3  # VDD
    mcu[11] += gnd       # GND
    mcu[25] += gnd       # GND
    mcu[50] += gnd       # GND
    mcu[75] += gnd       # GND
    
    # Decoupling
    cap1[1] += vcc_3v3
    cap1[2] += gnd
    cap2[1] += vcc_3v3
    cap2[2] += gnd
    
    # Crystal connections
    crystal[1] += mcu[23]  # OSC_IN
    crystal[2] += mcu[24]  # OSC_OUT
    
    cap_xtal1[1] += mcu[23]
    cap_xtal1[2] += gnd
    cap_xtal2[1] += mcu[24] 
    cap_xtal2[2] += gnd
