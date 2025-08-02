#!/usr/bin/env python3
"""
ESP32-C6 Circuit
Professional ESP32-C6 microcontroller with USB signal integrity and support circuitry
"""

from circuit_synth import *
from debug_header import debug_header
from led_blinker import led_blinker

@circuit(name="ESP32_C6_MCU")
def esp32c6(vcc_3v3, gnd, usb_dp, usb_dm):
    """
    ESP32-C6 microcontroller subcircuit with decoupling and connections
    
    Args:
        vcc_3v3: 3.3V power supply net
        gnd: Ground net
        usb_dp: USB Data+ net
        usb_dm: USB Data- net
    """
    
    # ESP32-C6 MCU
    esp32_c6 = Component(
        symbol="RF_Module:ESP32-C6-MINI-1",
        ref="U", 
        footprint="RF_Module:ESP32-C6-MINI-1"
    )

    # ESP32-C6 decoupling capacitor
    cap_esp = Component(
        symbol="Device:C", 
        ref="C", 
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # USB D+/D- inline resistors (22R for signal integrity)
    usb_dp_resistor = Component(symbol="Device:R", ref="R", value="22",
                               footprint="Resistor_SMD:R_0603_1608Metric")
    usb_dm_resistor = Component(symbol="Device:R", ref="R", value="22",
                               footprint="Resistor_SMD:R_0603_1608Metric")

    # Internal USB data nets (after ESD, before MCU)
    usb_dp_mcu = Net('USB_DP_MCU')
    usb_dm_mcu = Net('USB_DM_MCU')

    # Debug signals
    debug_tx = Net('DEBUG_TX')
    debug_rx = Net('DEBUG_RX')
    debug_en = Net('DEBUG_EN')
    debug_io0 = Net('DEBUG_IO0')
    
    # LED control
    led_control = Net('LED_CONTROL')
    
    # Power connections
    esp32_c6["3V3"] += vcc_3v3
    esp32_c6["GND"] += gnd
    
    # USB D+/D- inline resistors (ESD protected signal -> 22R -> MCU)
    usb_dp_resistor[1] += usb_dp
    usb_dp_resistor[2] += usb_dp_mcu
    usb_dm_resistor[1] += usb_dm
    usb_dm_resistor[2] += usb_dm_mcu
    
    # USB connections to MCU
    esp32_c6["IO18"] += usb_dp_mcu  # USB D+
    esp32_c6["IO19"] += usb_dm_mcu  # USB D-
    
    # Debug connections
    esp32_c6["EN"] += debug_en    # Reset/Enable
    esp32_c6["TXD0"] += debug_tx  # UART TX
    esp32_c6["RXD0"] += debug_rx  # UART RX
    esp32_c6["IO0"] += debug_io0  # Boot mode control
    
    # LED control GPIO
    esp32_c6["IO8"] += led_control  # GPIO for LED control
    

    cap_esp[1] += vcc_3v3
    cap_esp[2] += gnd


    debug_header_circuit = debug_header(vcc_3v3, gnd, debug_tx, debug_rx, debug_en, debug_io0)
    led_blinker_circuit = led_blinker(vcc_3v3, gnd, led_control)


