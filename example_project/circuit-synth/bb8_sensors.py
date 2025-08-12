#!/usr/bin/env python3
"""
BB-8 Sensor System
IMU sensor for balance and orientation
"""

from circuit_synth import *

@circuit(name="bb8_sensors")
def sensor_system():
    """
    IMU sensor system for BB-8 balance and orientation
    
    Features:
    - MPU-6050 6-axis IMU (gyro + accel)
    - I2C interface to ESP32
    - Interrupt capability
    - Temperature sensing
    """
    
    # Power and communication nets
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    i2c_sda = Net('I2C_SDA')
    i2c_scl = Net('I2C_SCL')
    
    # MPU-6050 IMU Sensor
    imu = Component(
        ref="U1",
        symbol="Sensor_Motion:MPU-6050",
        footprint="Sensor_Motion:InvenSense_QFN-24_4x4mm_P0.5mm",
        value="MPU-6050"
    )
    
    # Power connections
    imu['VCC'] += vcc_3v3
    imu['GND'] += gnd
    imu['VLOGIC'] += vcc_3v3
    
    # I2C connections
    imu['SDA'] += i2c_sda
    imu['SCL'] += i2c_scl
    
    # Address select (connect to GND for 0x68)
    imu['AD0'] += gnd
    
    # Interrupt output
    imu_int = Net('IMU_INT')
    imu['INT'] += imu_int
    
    # I2C pull-up resistors
    r_sda_pullup = Component(
        ref="R1",
        symbol="Device:R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="4.7k"
    )
    r_sda_pullup[1] += vcc_3v3
    r_sda_pullup[2] += i2c_sda
    
    r_scl_pullup = Component(
        ref="R2",
        symbol="Device:R",
        footprint="Resistor_SMD:R_0603_1608Metric", 
        value="4.7k"
    )
    r_scl_pullup[1] += vcc_3v3
    r_scl_pullup[2] += i2c_scl
    
    # Power supply decoupling
    c_vcc = Component(
        ref="C1",
        symbol="Device:C",
        footprint="Capacitor_SMD:C_0603_1608Metric",
        value="100nF"
    )
    c_vcc[1] += vcc_3v3
    c_vcc[2] += gnd
    
    c_bulk = Component(
        ref="C2",
        symbol="Device:C",
        footprint="Capacitor_SMD:C_0805_2012Metric",
        value="10uF"  
    )
    c_bulk[1] += vcc_3v3
    c_bulk[2] += gnd
    
    # Status LED for IMU activity
    led_imu = Component(
        ref="D1",
        symbol="Device:LED",
        footprint="LED_SMD:LED_0603_1608Metric",
        value="YELLOW"
    )
    
    r_led = Component(
        ref="R3",
        symbol="Device:R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="1k"
    )
    
    r_led[1] += imu_int
    r_led[2] += led_imu[1]  # Anode
    led_imu[2] += gnd  # Cathode
    
    # I2C expansion header for additional sensors
    i2c_header = Component(
        ref="J1",
        symbol="Connector:Conn_01x04_Male",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
        value="I2C_EXP"
    )
    
    i2c_header[1] += vcc_3v3  # VCC
    i2c_header[2] += gnd      # GND
    i2c_header[3] += i2c_sda  # SDA  
    i2c_header[4] += i2c_scl  # SCL
    
    return {
        'i2c_nets': {
            'I2C_SDA': i2c_sda,
            'I2C_SCL': i2c_scl,
            'IMU_INT': imu_int
        }
    }