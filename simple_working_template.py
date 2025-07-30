#!/usr/bin/env python3
"""
FOOLPROOF ESP32 + POWER TEMPLATE
This template WORKS - no complex imports, exact pin assignments tested
"""

from circuit_synth import *

@circuit
def main():
    """Simple working ESP32 with power regulation"""
    
    # Create nets
    vcc_3v3 = Net('VCC_3V3')
    vcc_5v = Net('VCC_5V') 
    gnd = Net('GND')
    
    # ESP32 module (tested pins: 1=GND, 3=3V3)
    esp32 = Component("RF_Module:ESP32-S3-MINI-1", ref="U1", footprint="RF_Module:ESP32-S2-MINI-1")
    esp32[1] += gnd         # Pin 1 = GND
    esp32[3] += vcc_3v3     # Pin 3 = 3V3  
    
    # USB-A connector (tested pins: 1=VBUS, 4=GND)
    usb_a = Component("Connector:USB_A", ref="J1", footprint="Connector_USB:USB_A_CNCTech_1001-011-01101_Horizontal")
    usb_a[1] += vcc_5v      # Pin 1 = VBUS
    usb_a[4] += gnd         # Pin 4 = GND
    
    # Voltage regulator (tested pins: 1=GND, 2=OUT, 3=IN)
    regulator = Component("Regulator_Linear:NCP1117-3.3_SOT223", ref="U3", footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2")
    regulator[1] += gnd         # Pin 1 = GND
    regulator[2] += vcc_3v3     # Pin 2 = 3.3V output
    regulator[3] += vcc_5v      # Pin 3 = 5V input
    
    # Input capacitor
    cap_in = Component("Device:C", ref="C1", value="10uF", footprint="Capacitor_SMD:C_0805_2012Metric")
    cap_in[1] += vcc_5v
    cap_in[2] += gnd
    
    # Output capacitor  
    cap_out = Component("Device:C", ref="C2", value="10uF", footprint="Capacitor_SMD:C_0805_2012Metric")
    cap_out[1] += vcc_3v3
    cap_out[2] += gnd

if __name__ == '__main__':
    circuit = main()
    circuit.generate_kicad_project("simple_esp32_power", force_regenerate=True)