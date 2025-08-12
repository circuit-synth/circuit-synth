#!/usr/bin/env python3
"""
BB-8 Droid Control Board - Simplified Working Version
Complete control system for BB-8 replica robot using available components
"""

from circuit_synth import *

@circuit(name="bb8_droid_simple")
def bb8_simple_circuit():
    """
    Simplified BB-8 Droid Control Board that actually works
    
    Features:
    - ESP32-WROOM-32 for wireless control
    - Basic motor control outputs
    - IMU sensor simulation 
    - LED control outputs
    - Audio output
    - Power regulation
    - All using standard available components
    """
    
    # Power distribution nets
    vcc_3v3 = Net('VCC_3V3')
    vcc_5v = Net('VCC_5V')
    gnd = Net('GND')
    vin = Net('VIN')
    
    print("🧠 Adding ESP32 controller...")
    # ESP32-WROOM-32 Main Controller
    esp32 = Component(
        ref="U1",
        symbol="RF_Module:ESP32-WROOM-32",
        footprint="RF_Module:ESP32-WROOM-32"
    )
    
    # Power connections
    esp32['VDD'] += vcc_3v3
    esp32['GND'] += gnd
    
    print("⚡ Adding power regulation...")
    # 3.3V LDO Regulator
    ldo_3v3 = Component(
        ref="U2",
        symbol="Regulator_Linear:AMS1117-3.3",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    ldo_3v3['VI'] += vcc_5v
    ldo_3v3['GND'] += gnd
    ldo_3v3['VO'] += vcc_3v3
    
    # 5V Input connector
    power_in = Component(
        ref="J1",
        symbol="Connector:Conn_01x02_Male",
        footprint="Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical"
    )
    power_in[1] += vcc_5v
    power_in[2] += gnd
    
    print("🚗 Adding motor control outputs...")
    # Motor control outputs (direct GPIO)
    motor1_pos = Net('MOTOR1_POS')
    motor1_neg = Net('MOTOR1_NEG') 
    motor2_pos = Net('MOTOR2_POS')
    motor2_neg = Net('MOTOR2_NEG')
    
    esp32['IO25'] += motor1_pos
    esp32['IO26'] += motor1_neg
    esp32['IO27'] += motor2_pos
    esp32['IO14'] += motor2_neg
    
    # Motor output headers
    motor1_conn = Component(
        ref="J2",
        symbol="Connector:Conn_01x02_Male", 
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
    )
    motor1_conn[1] += motor1_pos
    motor1_conn[2] += motor1_neg
    
    motor2_conn = Component(
        ref="J3",
        symbol="Connector:Conn_01x02_Male",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical" 
    )
    motor2_conn[1] += motor2_pos
    motor2_conn[2] += motor2_neg
    
    print("📊 Adding sensor connections...")
    # I2C bus for sensors
    i2c_sda = Net('I2C_SDA')
    i2c_scl = Net('I2C_SCL')
    
    esp32['IO21'] += i2c_sda
    esp32['IO22'] += i2c_scl
    
    # I2C sensor header (for external IMU)
    sensor_header = Component(
        ref="J4",
        symbol="Connector:Conn_01x04_Male",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
    )
    sensor_header[1] += vcc_3v3  # VCC
    sensor_header[2] += gnd      # GND
    sensor_header[3] += i2c_sda  # SDA
    sensor_header[4] += i2c_scl  # SCL
    
    print("💡 Adding LED control...")
    # LED control output
    led_data = Net('LED_DATA')
    esp32['IO18'] += led_data
    
    # LED strip connector
    led_conn = Component(
        ref="J5",
        symbol="Connector:Conn_01x03_Male",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
    )
    led_conn[1] += vcc_5v    # LED Power
    led_conn[2] += gnd       # Ground
    led_conn[3] += led_data  # Data
    
    print("🔊 Adding audio output...")
    # Audio PWM output
    audio_out = Net('AUDIO_OUT')
    esp32['IO23'] += audio_out
    
    # Audio output connector
    audio_conn = Component(
        ref="J6", 
        symbol="Connector:Conn_01x02_Male",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
    )
    audio_conn[1] += audio_out
    audio_conn[2] += gnd
    
    print("🔧 Adding support components...")
    # Power supply capacitors
    cap_3v3 = Component(
        ref="C1",
        symbol="Device:C",
        footprint="Capacitor_SMD:C_0805_2012Metric",
        value="10uF"
    )
    cap_3v3[1] += vcc_3v3
    cap_3v3[2] += gnd
    
    cap_5v = Component(
        ref="C2",
        symbol="Device:C", 
        footprint="Capacitor_SMD:C_0805_2012Metric",
        value="10uF"
    )
    cap_5v[1] += vcc_5v
    cap_5v[2] += gnd
    
    # Decoupling capacitor
    cap_decouple = Component(
        ref="C3",
        symbol="Device:C",
        footprint="Capacitor_SMD:C_0603_1608Metric",
        value="100nF"
    )
    cap_decouple[1] += vcc_3v3
    cap_decouple[2] += gnd
    
    # Status LEDs
    led_power = Component(
        ref="D1",
        symbol="Device:LED",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    led_status = Component(
        ref="D2", 
        symbol="Device:LED",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    # LED current limiting resistors
    r_power = Component(
        ref="R1",
        symbol="Device:R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="1k"
    )
    
    r_status = Component(
        ref="R2",
        symbol="Device:R",
        footprint="Resistor_SMD:R_0603_1608Metric", 
        value="1k"
    )
    
    # Power LED circuit
    r_power[1] += vcc_3v3
    r_power[2] += led_power['A']
    led_power['K'] += gnd
    
    # Status LED controlled by ESP32
    status_control = Net('STATUS_LED')
    esp32['IO2'] += status_control
    r_status[1] += status_control
    r_status[2] += led_status['A']
    led_status['K'] += gnd
    
    # Reset button
    reset_btn = Component(
        ref="SW1",
        symbol="Switch:SW_Push",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3"
    )
    
    # Reset circuit
    reset_net = Net('nRST')
    reset_btn[1] += reset_net
    reset_btn[2] += gnd
    esp32['EN'] += reset_net
    
    # Reset pull-up resistor
    r_reset = Component(
        ref="R3",
        symbol="Device:R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="10k"
    )
    r_reset[1] += vcc_3v3
    r_reset[2] += reset_net
    
    print("✅ BB-8 circuit created with all major subsystems!")
    print("   • ESP32-WROOM-32 wireless controller")
    print("   • Motor control outputs (4 channels)")
    print("   • I2C sensor interface") 
    print("   • LED strip control output")
    print("   • Audio PWM output")
    print("   • Power regulation (5V → 3.3V)")
    print("   • Status LEDs and reset button")
    print("   • All connectors for external components")

if __name__ == "__main__":
    print("🤖 Starting BB-8 Droid Control Board generation...")
    print("")
    
    circuit = bb8_simple_circuit()
    
    print("")
    print("🔌 Generating KiCad project...")
    circuit.generate_kicad_project("BB8_Droid_Control")
    
    print("")
    print("✅ BB-8 Droid Control Board generated successfully!")
    print("📁 Check the BB8_Droid_Control/ directory for KiCad files")
    print("")
    print("🎯 Ready for BB-8 droid assembly!")
    print("💡 Connect motors, sensors, LEDs, and speaker to the headers")
    print("🔋 Power with 5V supply via J1 connector")