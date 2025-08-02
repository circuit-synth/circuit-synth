#!/usr/bin/env python3
"""
MCU section for 08_reference

ESP32 microcontroller with basic connections and decoupling.
"""

from circuit_synth import *

@circuit(name="mcu_section")
def mcu_circuit(VCC_3V3, GND, USB_DP, USB_DM):
    """ESP32 microcontroller with basic connections"""
    
    # ESP32-C6 Mini module
    esp32 = Component(
        symbol="RF_Module:ESP32-C6-MINI-1",
        ref="U",
        footprint="RF_Module:ESP32-C6-MINI-1"
    )
    
    # Decoupling capacitors
    cap1 = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    cap2 = Component(
        symbol="Device:C",
        ref="C", 
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Connect ESP32 power
    esp32["3V3"] += VCC_3V3       # Main power supply
    esp32["GND"] += GND           # Ground
    esp32["IO18"] += USB_DP       # USB D+ (GPIO18)
    esp32["IO19"] += USB_DM       # USB D- (GPIO19)
    
    # Connect decoupling capacitors
    cap1[1] += VCC_3V3
    cap1[2] += GND
    
    cap2[1] += VCC_3V3 
    cap2[2] += GND