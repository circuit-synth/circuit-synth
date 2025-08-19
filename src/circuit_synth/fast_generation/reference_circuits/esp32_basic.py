#!/usr/bin/env python3
"""
ESP32 Basic Development Board - Reference Circuit
Professional ESP32-S3 microcontroller board with USB-C, decoupling, and debug
"""

from circuit_synth import *

@circuit(name="ESP32_Basic_Board")
def esp32_basic(VCC_3V3, VCC_5V, GND, USB_DP, USB_DM):
    """
    Basic ESP32-S3 development board with essential components
    - ESP32-S3 microcontroller  
    - USB-C connector for power and programming
    - Decoupling capacitors
    - Debug header
    """
    
    
    # ESP32-S3 microcontroller
    esp32 = Component(
        symbol="RF_Module:ESP32-S3-WROOM-1",
        ref="U",
        footprint="RF_Module:ESP32-S3-WROOM-1"
    )
    
    # USB-C connector for power and data
    usb_connector = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P",
        ref="J", 
        footprint="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12"
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
    
    # EN pull-up resistor
    en_pullup = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Debug header for programming
    debug_header = Component(
        symbol="Connector_Generic:Conn_01x04",
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
    )
    
    # Power connections
    esp32["3V3"] += VCC_3V3
    esp32["GND"] += GND

    # USB connector power
    usb_connector["VBUS"] += VCC_5V
    usb_connector["GND"] += GND
    
    # USB data connections
    usb_connector["D+"] += USB_DP
    usb_connector["D-"] += USB_DM
    esp32["USB_D+"] += USB_DP  # USB D+
    esp32["USB_D-"] += USB_DM  # USB D-


    
    # Power supply decoupling
    cap_bulk["1"] += VCC_3V3
    cap_bulk["2"] += GND
    cap_bypass1["1"] += VCC_3V3
    cap_bypass1["2"] += GND
    cap_bypass2["1"] += VCC_3V3
    cap_bypass2["2"] += GND
    
    # EN pull-up
    en_pullup["1"] += VCC_3V3
    en_pullup["2"] += esp32["EN"]

    # Debug header connections
    debug_header["1"] += VCC_3V3  # Power
    debug_header["2"] += GND      # Ground
    debug_header["3"] += esp32["TXD0"]  # UART TX
    debug_header["4"] += esp32["RXD0"]  # UART RX


@circuit(name="ESP32_Basic_Test")
def test_esp32_basic():
    # Create nets for testing    
    vcc_3v3 = Net('VCC_3V3')
    vcc_5v = Net('VCC_5V')
    gnd = Net('GND')
    usb_dp = Net('USB_DP')
    usb_dm = Net('USB_DM')
    
    esp32_basic(vcc_3v3, vcc_5v, gnd, usb_dp, usb_dm)

if __name__ == "__main__":
    circuit_obj = test_esp32_basic()
    circuit_obj.generate_kicad_project(project_name="ESP32_Basic_Board")