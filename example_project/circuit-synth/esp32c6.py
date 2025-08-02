#!/usr/bin/env python3
"""
ESP32-C6 Circuit
Professional ESP32-C6 microcontroller with support circuitry
"""

from circuit_synth import *

@circuit(name="ESP32_C6_MCU")
def esp32c6(vcc_3v3, gnd, usb_dp, usb_dm, debug_tx, debug_rx, debug_en, debug_io0, led_control):
    """
    ESP32-C6 microcontroller subcircuit with decoupling and connections
    
    Args:
        vcc_3v3: 3.3V power supply net
        gnd: Ground net
        usb_dp: USB Data+ net
        usb_dm: USB Data- net
        debug_tx: Debug UART TX net
        debug_rx: Debug UART RX net
        debug_en: Reset/Enable net
        debug_io0: Boot mode control net
        led_control: LED control GPIO net
    """
    
    # ESP32-C6 MCU
    esp32_c6 = Component(
        symbol="RF_Module:ESP32-C6-MINI-1",
        ref="U", 
        footprint="RF_Module:ESP32-C6-MINI-1"
    )
    
    # Power connections
    esp32_c6["3V3"] += vcc_3v3
    esp32_c6["GND"] += gnd
    
    # USB connections
    esp32_c6["IO18"] += usb_dp  # USB D+
    esp32_c6["IO19"] += usb_dm  # USB D-
    
    # Debug connections
    esp32_c6["EN"] += debug_en    # Reset/Enable
    esp32_c6["TXD0"] += debug_tx  # UART TX
    esp32_c6["RXD0"] += debug_rx  # UART RX
    esp32_c6["IO0"] += debug_io0  # Boot mode control
    
    # LED control GPIO
    esp32_c6["IO8"] += led_control  # GPIO for LED control
    
    # ESP32-C6 decoupling capacitor
    cap_esp = Component(
        symbol="Device:C", 
        ref="C", 
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    cap_esp[1] += vcc_3v3
    cap_esp[2] += gnd
