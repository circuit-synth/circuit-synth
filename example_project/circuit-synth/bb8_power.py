#!/usr/bin/env python3
"""
BB-8 Power Management System
Handles battery management, USB-C charging, and power regulation
"""

from circuit_synth import *

@circuit(name="bb8_power_management")
def power_management():
    """
    Complete power management for BB-8 droid
    
    Features:
    - TP4056 Li-ion battery charger
    - Battery protection circuit
    - 5V boost converter for motors/LEDs
    - 3.3V LDO for microcontroller
    - USB-C charging interface
    """
    
    # Define power nets
    vbat = Net('VBAT')          # Battery voltage
    vbus = Net('VBUS')          # USB 5V input  
    vcc_5v = Net('VCC_5V')      # Regulated 5V
    vcc_3v3 = Net('VCC_3V3')    # Regulated 3.3V
    gnd = Net('GND')            # Ground
    
    # USB-C Connector for charging
    usb_connector = Component(
        ref="J1",
        symbol="Connector:USB_C_Receptacle_USB2.0_16P",
        footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
        value="USB-C"
    )
    
    usb_connector['VBUS'] += vbus
    usb_connector['GND'] += gnd
    
    # TP4056 Battery Charger
    charger = Component(
        ref="U1",
        symbol="Battery_Management:TP4056",
        footprint="Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm",
        value="TP4056"
    )
    
    charger['VCC'] += vbus
    charger['GND'] += gnd
    charger['BAT'] += vbat
    
    # Charge current programming resistor (1.2kΩ = 1A)
    r_prog = Component(
        ref="R1",
        symbol="Device:R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="1.2k"
    )
    charger['PROG'] += r_prog[1]
    r_prog[2] += gnd
    
    # Battery connector
    battery_conn = Component(
        ref="J2",
        symbol="Connector:Conn_01x02_Male",
        footprint="Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical",
        value="BATTERY"
    )
    battery_conn[1] += vbat
    battery_conn[2] += gnd
    
    # 5V Boost Converter - MT3608
    boost_converter = Component(
        ref="U2",
        symbol="Regulator_Switching:MT3608",
        footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
        value="MT3608"
    )
    
    boost_converter['VIN'] += vbat
    boost_converter['GND'] += gnd
    boost_converter['VOUT'] += vcc_5v
    boost_converter['EN'] += vbat  # Always enabled
    
    # Boost inductor
    inductor = Component(
        ref="L1",
        symbol="Device:L",
        footprint="Inductor_SMD:L_1210_3225Metric",
        value="22uH"
    )
    inductor[1] += boost_converter['SW']
    inductor[2] += vcc_5v
    
    # 3.3V LDO Regulator - AMS1117
    ldo_regulator = Component(
        ref="U3",
        symbol="Regulator_Linear:AMS1117-3.3",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
        value="AMS1117-3.3"
    )
    
    ldo_regulator['VIN'] += vcc_5v
    ldo_regulator['GND'] += gnd
    ldo_regulator['VOUT'] += vcc_3v3
    
    # Power supply capacitors
    # 5V rail bulk capacitor
    c_5v_bulk = Component(
        ref="C1",
        symbol="Device:C",
        footprint="Capacitor_SMD:C_1206_3216Metric",
        value="470uF"
    )
    c_5v_bulk[1] += vcc_5v
    c_5v_bulk[2] += gnd
    
    # 5V rail ceramic capacitor
    c_5v_ceramic = Component(
        ref="C2",
        symbol="Device:C", 
        footprint="Capacitor_SMD:C_0603_1608Metric",
        value="100nF"
    )
    c_5v_ceramic[1] += vcc_5v
    c_5v_ceramic[2] += gnd
    
    # 3.3V rail capacitors
    c_3v3_input = Component(
        ref="C3",
        symbol="Device:C",
        footprint="Capacitor_SMD:C_0603_1608Metric", 
        value="100nF"
    )
    c_3v3_input[1] += vcc_5v
    c_3v3_input[2] += gnd
    
    c_3v3_output = Component(
        ref="C4",
        symbol="Device:C",
        footprint="Capacitor_SMD:C_0805_2012Metric",
        value="10uF"
    )
    c_3v3_output[1] += vcc_3v3
    c_3v3_output[2] += gnd
    
    # Battery input capacitor
    c_battery = Component(
        ref="C5",
        symbol="Device:C",
        footprint="Capacitor_SMD:C_0603_1608Metric",
        value="100nF"
    )
    c_battery[1] += vbat
    c_battery[2] += gnd
    
    # Status LEDs
    led_charging = Component(
        ref="D1",
        symbol="Device:LED",
        footprint="LED_SMD:LED_0603_1608Metric",
        value="RED"
    )
    
    r_led_charging = Component(
        ref="R2",
        symbol="Device:R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="1k"
    )
    
    charger['CHRG'] += r_led_charging[1]
    r_led_charging[2] += led_charging[1]  # Anode
    led_charging[2] += gnd  # Cathode
    
    # Power good LED
    led_power = Component(
        ref="D2",
        symbol="Device:LED",
        footprint="LED_SMD:LED_0603_1608Metric",
        value="GREEN"
    )
    
    r_led_power = Component(
        ref="R3",
        symbol="Device:R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="1k"
    )
    
    r_led_power[1] += vcc_5v
    r_led_power[2] += led_power[1]  # Anode
    led_power[2] += gnd  # Cathode
    
    return {
        'nets': {
            'VBAT': vbat,
            'VBUS': vbus,
            'VCC_5V': vcc_5v,
            'VCC_3V3': vcc_3v3,
            'GND': gnd
        }
    }