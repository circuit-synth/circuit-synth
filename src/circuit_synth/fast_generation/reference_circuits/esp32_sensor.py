#!/usr/bin/env python3
"""
ESP32 Sensor Integration Board - Reference Circuit
ESP32-S3 with MPU-6050 IMU sensor and I2C pull-ups
"""

from circuit_synth import *

@circuit(name="ESP32_Sensor_Board")
def esp32_sensor(VCC_3V3, VCC_5V, GND, USB_DP, USB_DM):
    """
    ESP32-S3 with MPU-6050 IMU sensor integration
    - ESP32-S3 microcontroller
    - MPU-6050 6-axis IMU (accelerometer + gyroscope) 
    - I2C pull-up resistors
    """
    
    # Create internal I2C bus nets
    i2c_scl = Net('I2C_SCL')
    i2c_sda = Net('I2C_SDA')
    
    # ESP32-S3 microcontroller
    esp32 = Component(
        symbol="RF_Module:ESP32-S3-WROOM-1",
        ref="U",
        footprint="RF_Module:ESP32-S3-WROOM-1"
    )
    
    # MPU-6050 IMU sensor
    mpu6050 = Component(
        symbol="Sensor_Motion:MPU-6050",
        ref="U",
        footprint="Sensor_Motion:InvenSense_QFN-24_4x4mm_P0.5mm"
    )
    
    # I2C pull-up resistors (4.7k typical)
    pullup_scl = Component(
        symbol="Device:R",
        ref="R", 
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    pullup_sda = Component(
        symbol="Device:R",
        ref="R",
        value="4.7k", 
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Power supply decoupling
    cap_bulk = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Power connections
    esp32["3V3"] += VCC_3V3
    esp32["GND"] += GND
    mpu6050["VDD"] += VCC_3V3
    mpu6050["GND"] += GND
    
    # I2C connections between ESP32 and MPU6050
    esp32["GPIO21"] += i2c_sda  # ESP32 I2C SDA
    esp32["GPIO22"] += i2c_scl  # ESP32 I2C SCL
    mpu6050["SDA"] += i2c_sda   # MPU6050 I2C SDA
    mpu6050["SCL"] += i2c_scl   # MPU6050 I2C SCL
    
    # I2C pull-up resistors
    pullup_scl["1"] += VCC_3V3
    pullup_scl["2"] += i2c_scl
    pullup_sda["1"] += VCC_3V3  
    pullup_sda["2"] += i2c_sda
    
    # Power supply decoupling
    cap_bulk["1"] += VCC_3V3
    cap_bulk["2"] += GND
    
    # MPU6050 address selection (tie AD0 low for 0x68 address)
    mpu6050["AD0"] += GND


if __name__ == "__main__":
    # Create nets for standalone testing
    vcc_3v3 = Net('VCC_3V3')
    vcc_5v = Net('VCC_5V')
    gnd = Net('GND') 
    usb_dp = Net('USB_DP')
    usb_dm = Net('USB_DM')
    
    circuit_obj = esp32_sensor(vcc_3v3, vcc_5v, gnd, usb_dp, usb_dm)
    circuit_obj.generate_kicad_project(project_name="ESP32_Sensor_Board")