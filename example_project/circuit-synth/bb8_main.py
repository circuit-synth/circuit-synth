#!/usr/bin/env python3
"""
BB-8 Droid Control Board - Main Circuit
Complete control system for BB-8 replica robot
"""

from circuit_synth import *

@circuit(name="bb8_droid_control_board")
def bb8_main_circuit():
    """
    Complete BB-8 Droid Control Board
    
    Features:
    - ESP32-WROOM-32 for wireless control and processing
    - Dual motor drivers for ball rolling mechanism
    - IMU sensor for balance and orientation
    - RGB LED arrays for head and body lighting
    - Audio amplifier for sound effects
    - Battery management with USB-C charging
    - Servo control for head movement
    """
    
    # Power distribution nets
    vcc_3v3 = Net('VCC_3V3')
    vcc_5v = Net('VCC_5V')
    vbat = Net('VBAT')
    gnd = Net('GND')
    usb_vbus = Net('USB_VBUS')
    
    # ESP32-WROOM-32 Main Controller
    esp32 = Component(
        ref="U1",
        symbol="RF_Module:ESP32-WROOM-32",
        footprint="RF_Module:ESP32-WROOM-32",
        value="ESP32-WROOM-32"
    )
    
    # Power connections
    esp32['VDD'] += vcc_3v3
    esp32['GND'] += gnd
    
    # Motor control pins
    motor1_in1 = Net('MOTOR1_IN1')
    motor1_in2 = Net('MOTOR1_IN2')
    motor2_in1 = Net('MOTOR2_IN1')
    motor2_in2 = Net('MOTOR2_IN2')
    
    esp32['IO25'] += motor1_in1
    esp32['IO26'] += motor1_in2
    esp32['IO27'] += motor2_in1
    esp32['IO14'] += motor2_in2
    
    # DRV8833 Motor Driver 1
    motor_driver1 = Component(
        ref="U2",
        symbol="Driver_Motor:DRV8833",
        footprint="Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
        value="DRV8833"
    )
    
    motor_driver1['VCC'] += vcc_5v
    motor_driver1['AVDD'] += vcc_3v3
    motor_driver1['GND'] += gnd
    motor_driver1['AIN1'] += motor1_in1
    motor_driver1['AIN2'] += motor1_in2
    
    # DRV8833 Motor Driver 2  
    motor_driver2 = Component(
        ref="U3",
        symbol="Driver_Motor:DRV8833",
        footprint="Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
        value="DRV8833"
    )
    
    motor_driver2['VCC'] += vcc_5v
    motor_driver2['AVDD'] += vcc_3v3
    motor_driver2['GND'] += gnd
    motor_driver2['AIN1'] += motor2_in1
    motor_driver2['AIN2'] += motor2_in2
    
    # IMU Sensor - MPU6050
    imu = Component(
        ref="U4",
        symbol="Sensor_Motion:MPU-6050",
        footprint="Sensor_Motion:InvenSense_QFN-24_4x4mm_P0.5mm",
        value="MPU-6050"
    )
    
    # I2C connections
    i2c_sda = Net('I2C_SDA')
    i2c_scl = Net('I2C_SCL')
    
    imu['VCC'] += vcc_3v3
    imu['GND'] += gnd
    imu['SDA'] += i2c_sda
    imu['SCL'] += i2c_scl
    
    esp32['IO21'] += i2c_sda
    esp32['IO22'] += i2c_scl
    
    # Audio Amplifier - MAX98357A
    audio_amp = Component(
        ref="U5",
        symbol="Audio:MAX98357A",
        footprint="Package_DFN_QFN:QFN-16-1EP_3x3mm_P0.5mm",
        value="MAX98357A"
    )
    
    # I2S connections
    i2s_bclk = Net('I2S_BCLK')
    i2s_lrclk = Net('I2S_LRCLK')
    i2s_din = Net('I2S_DIN')
    
    audio_amp['VDD'] += vcc_5v
    audio_amp['GND'] += gnd
    audio_amp['BCLK'] += i2s_bclk
    audio_amp['LRC'] += i2s_lrclk
    audio_amp['DIN'] += i2s_din
    
    esp32['IO23'] += i2s_din
    esp32['IO5'] += i2s_lrclk
    esp32['IO4'] += i2s_bclk
    
    # LED Control - Level Shifter for WS2812B
    level_shifter = Component(
        ref="U6",
        symbol="74xx:74HCT125",
        footprint="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
        value="74HCT125"
    )
    
    led_data_in = Net('LED_DATA_IN')
    led_data_out = Net('LED_DATA_OUT')
    
    level_shifter['VCC'] += vcc_5v
    level_shifter['GND'] += gnd
    level_shifter['1A'] += led_data_in
    level_shifter['1Y'] += led_data_out
    level_shifter['1OE'] += gnd
    
    esp32['IO18'] += led_data_in
    
    # Power Management - TP4056 Battery Charger
    charger = Component(
        ref="U7",
        symbol="Battery_Management:TP4056",
        footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
        value="TP4056"
    )
    
    charger['VCC'] += usb_vbus
    charger['GND'] += gnd
    charger['BAT'] += vbat
    
    # 5V Boost Converter - MT3608
    boost_5v = Component(
        ref="U8",
        symbol="Regulator_Switching:MT3608",
        footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
        value="MT3608"
    )
    
    boost_5v['VIN'] += vbat
    boost_5v['GND'] += gnd
    boost_5v['VOUT'] += vcc_5v
    
    # 3.3V LDO Regulator - AMS1117
    ldo_3v3 = Component(
        ref="U9",
        symbol="Regulator_Linear:AMS1117-3.3",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
        value="AMS1117-3.3"
    )
    
    ldo_3v3['VIN'] += vcc_5v
    ldo_3v3['GND'] += gnd
    ldo_3v3['VOUT'] += vcc_3v3
    
    # USB-C Connector
    usb_c = Component(
        ref="J1",
        symbol="Connector:USB_C_Receptacle_USB2.0",
        footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
        value="USB-C"
    )
    
    usb_c['VBUS'] += usb_vbus
    usb_c['GND'] += gnd
    
    # Battery Connector
    battery_conn = Component(
        ref="J2",
        symbol="Connector:Conn_01x02_Male",
        footprint="Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical",
        value="BATTERY"
    )
    
    battery_conn[1] += vbat
    battery_conn[2] += gnd
    
    # Motor Connectors
    motor1_conn = Component(
        ref="J3",
        symbol="Connector:Conn_01x02_Male",
        footprint="Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical",
        value="MOTOR1"
    )
    
    motor2_conn = Component(
        ref="J4",
        symbol="Connector:Conn_01x02_Male",
        footprint="Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical",
        value="MOTOR2"
    )
    
    # LED Strip Connector
    led_conn = Component(
        ref="J5",
        symbol="Connector:Conn_01x03_Male",
        footprint="Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical",
        value="LED_STRIP"
    )
    
    led_conn[1] += vcc_5v
    led_conn[2] += gnd
    led_conn[3] += led_data_out
    
    # Speaker Connector
    speaker_conn = Component(
        ref="J6",
        symbol="Connector:Conn_01x02_Male",
        footprint="Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical",
        value="SPEAKER"
    )
    
    # Power decoupling capacitors
    cap1 = Component(
        ref="C1",
        symbol="Device:C",
        footprint="Capacitor_SMD:C_0603_1608Metric",
        value="100nF"
    )
    cap1[1] += vcc_3v3
    cap1[2] += gnd
    
    cap2 = Component(
        ref="C2", 
        symbol="Device:C",
        footprint="Capacitor_SMD:C_0805_2012Metric",
        value="10uF"
    )
    cap2[1] += vcc_5v
    cap2[2] += gnd

if __name__ == "__main__":
    print("🤖 Generating BB-8 Droid Control Board...")
    circuit = bb8_main_circuit()
    circuit.generate_kicad_project("BB8_Droid_Control_Board")
    print("✅ BB-8 control board generated successfully!")