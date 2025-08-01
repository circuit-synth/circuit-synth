#!/usr/bin/env python3
"""
ESP32-C6 Subcircuit - Main microcontroller with decoupling
ESP32-C6 MINI-1 module with proper decoupling capacitor
"""

from circuit_synth import *

@circuit(name="ESP32_C6_MCU")
def esp32_c6_subcircuit(vcc_3v3=None, gnd=None, usb_dp=None, usb_dm=None, 
                       debug_tx=None, debug_rx=None, debug_en=None, debug_io0=None, 
                       led_control=None):
    """ESP32-C6 microcontroller with support circuits"""
    
    # Interface nets - use provided nets or create defaults for standalone operation
    vcc_3v3 = vcc_3v3 or Net('VCC_3V3')
    gnd = gnd or Net('GND')
    usb_dp = usb_dp or Net('USB_DP')
    usb_dm = usb_dm or Net('USB_DM')
    debug_tx = debug_tx or Net('DEBUG_TX')
    debug_rx = debug_rx or Net('DEBUG_RX')
    debug_en = debug_en or Net('DEBUG_EN')
    debug_io0 = debug_io0 or Net('DEBUG_IO0')
    led_control = led_control or Net('LED_CONTROL')
    
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
    cap_esp = Component(symbol="Device:C", ref="C", value="100nF",
                       footprint="Capacitor_SMD:C_0603_1608Metric")
    cap_esp[1] += vcc_3v3
    cap_esp[2] += gnd

if __name__ == "__main__":
    circuit = esp32_c6_subcircuit()
    circuit.generate_kicad_project("esp32_c6_mcu")
    print("✅ ESP32-C6 subcircuit generated!")