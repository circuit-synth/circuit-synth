from circuit_synth import *

@circuit(name="mcu_circuit")
def mcu_circuit(vcc_3v3, gnd):
    """ESP32 microcontroller circuit"""
    
    # ESP32 MCU module
    mcu = Component(
        symbol="RF_Module:ESP32-S3-MINI-1",
        ref="U2",
        footprint="RF_Module:ESP32-S2-MINI-1"
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
    
    # Power connections
    mcu[3] += vcc_3v3  # 3V3
    mcu[1] += gnd      # GND
    
    # Decoupling
    cap1[1] += vcc_3v3
    cap1[2] += gnd
    cap2[1] += vcc_3v3
    cap2[2] += gnd
