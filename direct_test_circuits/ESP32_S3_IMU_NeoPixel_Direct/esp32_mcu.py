#!/usr/bin/env python3
"""
ESP32 MCU Circuit
ESP32-S3 microcontroller with support circuitry
"""

from circuit_synth import *

@circuit(name="ESP32_MCU")
def esp32_mcu(vcc_3v3_in, gnd_in, usb_dp_in, usb_dm_in):
    """ESP32-S3 microcontroller subcircuit"""
    
    # Use input nets
    vcc_3v3 = vcc_3v3_in
    gnd = gnd_in
    usb_dp = usb_dp_in
    usb_dm = usb_dm_in
    
    # Create output nets for other subcircuits
    debug_tx = Net('DEBUG_TX')
    debug_rx = Net('DEBUG_RX') 
    led_control = Net('LED_CONTROL')
    
    # ESP32-S3 microcontroller
    esp32 = Component(
        symbol="RF_Module:ESP32-S3-WROOM-1",
        ref="U",
        footprint="RF_Module:ESP32-S3-WROOM-1"
    )
    
    # Decoupling capacitors
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
    
    # EN pull-up resistor
    en_pullup = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Power connections
    esp32["3V3"] += vcc_3v3
    esp32["GND"] += gnd
    
    # USB connections
    esp32["USB_D+"] += usb_dp
    esp32["USB_D-"] += usb_dm
    
    # Debug UART
    esp32["TXD0"] += debug_tx
    esp32["RXD0"] += debug_rx
    
    # LED control
    esp32["IO8"] += led_control
    
    # Power supply decoupling
    cap_bulk["1"] += vcc_3v3
    cap_bulk["2"] += gnd
    cap_bypass1["1"] += vcc_3v3
    cap_bypass1["2"] += gnd
    
    # EN pull-up
    en_pullup["1"] += vcc_3v3
    en_pullup["2"] += esp32["EN"]
    
    return vcc_3v3, gnd, debug_tx, debug_rx, led_control
