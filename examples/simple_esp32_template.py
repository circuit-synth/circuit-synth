#!/usr/bin/env python3
"""
Simple ESP32 + IMU + USB-C Template
This is the EXACT template that Claude should use - no deviations!
"""

from circuit_synth import *

@circuit  
def main():
    """Simple ESP32 development board with IMU and USB-C"""
    
    # Create nets
    vcc_3v3 = Net('VCC_3V3')
    vcc_5v = Net('VCC_5V') 
    gnd = Net('GND')
    sda = Net('SDA')
    scl = Net('SCL')
    usb_dp = Net('USB_DP')
    usb_dm = Net('USB_DM')
    
    # ESP32 module
    esp32 = Component("RF_Module:ESP32-S3-MINI-1", ref="U1", footprint="RF_Module:ESP32-S2-MINI-1")
    esp32[1] += gnd         # GND
    esp32[2] += vcc_3v3     # VCC  
    esp32[3] += sda         # SDA pin
    esp32[4] += scl         # SCL pin
    esp32[5] += usb_dp      # USB D+
    esp32[6] += usb_dm      # USB D-
    
    # IMU sensor
    imu = Component("Sensor_Motion:MPU-6050", ref="U2", footprint="Sensor_Motion:InvenSense_QFN-24_4x4mm_P0.5mm")
    imu[1] += vcc_3v3       # VDD
    imu[2] += gnd           # GND
    imu[3] += sda           # SDA
    imu[4] += scl           # SCL
    
    # USB-C connector
    usb_c = Component("Connector:USB_C_Receptacle_USB2.0", ref="J1", footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal")
    usb_c[1] += vcc_5v      # VBUS
    usb_c[2] += gnd         # GND
    usb_c[3] += usb_dp      # D+
    usb_c[4] += usb_dm      # D-
    
    # Voltage regulator (5V -> 3.3V)
    regulator = Component("Regulator_Linear:NCP1117-3.3_SOT223", ref="U3", footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2")
    regulator[1] += gnd         # GND
    regulator[2] += vcc_3v3     # 3.3V output
    regulator[3] += vcc_5v      # 5V input
    
    # Input capacitor
    cap_in = Component("Device:C", ref="C1", value="10uF", footprint="Capacitor_SMD:C_0805_2012Metric")
    cap_in[1] += vcc_5v
    cap_in[2] += gnd
    
    # Output capacitor  
    cap_out = Component("Device:C", ref="C2", value="10uF", footprint="Capacitor_SMD:C_0805_2012Metric")
    cap_out[1] += vcc_3v3
    cap_out[2] += gnd
    
    # I2C pullup resistors
    r_sda = Component("Device:R", ref="R1", value="4.7K", footprint="Resistor_SMD:R_0603_1608Metric")
    r_sda[1] += vcc_3v3
    r_sda[2] += sda
    
    r_scl = Component("Device:R", ref="R2", value="4.7K", footprint="Resistor_SMD:R_0603_1608Metric") 
    r_scl[1] += vcc_3v3
    r_scl[2] += scl

if __name__ == '__main__':
    circuit = main()
    circuit.generate_kicad_project("esp32_imu_dev_board", force_regenerate=True)