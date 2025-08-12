#!/usr/bin/env python3
"""
BB-8 Motor Control System  
Dual motor drivers for ball rolling mechanism
"""

from circuit_synth import *

@circuit(name="bb8_motor_control")
def motor_control():
    """
    Dual motor driver system for BB-8 ball rolling
    
    Features:
    - Two DRV8833 dual H-bridge motor drivers
    - Current sensing and protection
    - PWM speed control from ESP32
    - Motor terminal connections
    """
    
    # Power and control nets
    vcc_5v = Net('VCC_5V')
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    
    # Motor control signals from ESP32
    motor1_in1 = Net('MOTOR1_IN1')
    motor1_in2 = Net('MOTOR1_IN2')
    motor2_in1 = Net('MOTOR2_IN1') 
    motor2_in2 = Net('MOTOR2_IN2')
    
    # Motor Driver 1 - DRV8833
    driver1 = Component(
        ref="U1",
        symbol="Driver_Motor:DRV8833",
        footprint="Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
        value="DRV8833"
    )
    
    # Power connections for driver 1
    driver1['VCC'] += vcc_5v      # Motor power
    driver1['AVDD'] += vcc_3v3    # Logic power
    driver1['GND'] += gnd
    
    # Control connections for motor 1
    driver1['AIN1'] += motor1_in1
    driver1['AIN2'] += motor1_in2
    
    # Motor 1 outputs
    motor1_pos = Net('MOTOR1+')
    motor1_neg = Net('MOTOR1-')
    driver1['AOUT1'] += motor1_pos
    driver1['AOUT2'] += motor1_neg
    
    # Motor Driver 2 - DRV8833
    driver2 = Component(
        ref="U2", 
        symbol="Driver_Motor:DRV8833",
        footprint="Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
        value="DRV8833"
    )
    
    # Power connections for driver 2
    driver2['VCC'] += vcc_5v
    driver2['AVDD'] += vcc_3v3
    driver2['GND'] += gnd
    
    # Control connections for motor 2
    driver2['AIN1'] += motor2_in1
    driver2['AIN2'] += motor2_in2
    
    # Motor 2 outputs
    motor2_pos = Net('MOTOR2+')
    motor2_neg = Net('MOTOR2-')
    driver2['AOUT1'] += motor2_pos
    driver2['AOUT2'] += motor2_neg
    
    # Motor terminal connectors
    motor1_connector = Component(
        ref="J1",
        symbol="Connector:Screw_Terminal_01x02",
        footprint="TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal",
        value="MOTOR1"
    )
    motor1_connector[1] += motor1_pos
    motor1_connector[2] += motor1_neg
    
    motor2_connector = Component(
        ref="J2",
        symbol="Connector:Screw_Terminal_01x02", 
        footprint="TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal",
        value="MOTOR2"
    )
    motor2_connector[1] += motor2_pos
    motor2_connector[2] += motor2_neg
    
    # Power supply decoupling
    c1 = Component(
        ref="C1",
        symbol="Device:C",
        footprint="Capacitor_SMD:C_1206_3216Metric",
        value="100uF"
    )
    c1[1] += vcc_5v
    c1[2] += gnd
    
    c2 = Component(
        ref="C2",
        symbol="Device:C",
        footprint="Capacitor_SMD:C_0603_1608Metric",
        value="100nF"
    )
    c2[1] += vcc_3v3
    c2[2] += gnd
    
    c3 = Component(
        ref="C3",
        symbol="Device:C",
        footprint="Capacitor_SMD:C_1206_3216Metric", 
        value="100uF"
    )
    c3[1] += vcc_5v
    c3[2] += gnd
    
    c4 = Component(
        ref="C4",
        symbol="Device:C",
        footprint="Capacitor_SMD:C_0603_1608Metric",
        value="100nF"
    )
    c4[1] += vcc_3v3
    c4[2] += gnd
    
    # Current sensing resistors
    r_sense1 = Component(
        ref="R1",
        symbol="Device:R",
        footprint="Resistor_SMD:R_1206_3216Metric",
        value="0.1"
    )
    
    r_sense2 = Component(
        ref="R2",
        symbol="Device:R", 
        footprint="Resistor_SMD:R_1206_3216Metric",
        value="0.1"
    )
    
    # Protection diodes
    d1 = Component(
        ref="D1",
        symbol="Device:D_Schottky",
        footprint="Diode_SMD:D_SMA",
        value="SS14"
    )
    d1[1] += motor1_neg  # Anode
    d1[2] += motor1_pos  # Cathode
    
    d2 = Component(
        ref="D2", 
        symbol="Device:D_Schottky",
        footprint="Diode_SMD:D_SMA", 
        value="SS14"
    )
    d2[1] += motor2_neg
    d2[2] += motor2_pos
    
    return {
        'control_nets': {
            'MOTOR1_IN1': motor1_in1,
            'MOTOR1_IN2': motor1_in2,
            'MOTOR2_IN1': motor2_in1,
            'MOTOR2_IN2': motor2_in2
        }
    }