#!/usr/bin/env python3
"""
BB-8 Droid Control Board - Actually Working Version
Simple but functional BB-8 control circuit using verified components
"""

from circuit_synth import *

@circuit(name="BB8_Control_Board")
def bb8_working():
    """
    Working BB-8 Droid Control Board
    
    This circuit uses only verified components that actually exist
    in the KiCad symbol libraries to ensure it generates successfully.
    
    Features:
    - ESP32-WROOM-32 microcontroller
    - Power regulation (3.3V LDO)  
    - Motor control outputs
    - LED control
    - Basic components only
    """
    
    print("🧠 Creating ESP32 controller...")
    
    # Power nets
    vcc_3v3 = Net('VCC_3V3')
    vcc_5v = Net('VCC_5V') 
    gnd = Net('GND')
    
    # ESP32-WROOM-32 (verified working from existing circuit)
    esp32 = Component(
        symbol="RF_Module:ESP32-WROOM-32",
        ref="U1",
        footprint="RF_Module:ESP32-WROOM-32"
    )
    
    # Power connections
    esp32['VDD'] += vcc_3v3
    esp32['GND'] += gnd
    
    print("⚡ Adding power regulation...")
    
    # 3.3V LDO Regulator (verified working from existing circuit)
    ldo = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U2", 
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    ldo['VI'] += vcc_5v
    ldo['VO'] += vcc_3v3
    ldo['GND'] += gnd
    
    print("🔧 Adding support components...")
    
    # Power supply capacitors (verified symbols)
    cap_in = Component(
        symbol="Device:C",
        ref="C1",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    cap_in[1] += vcc_5v
    cap_in[2] += gnd
    
    cap_out = Component(
        symbol="Device:C", 
        ref="C2",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    cap_out[1] += vcc_3v3
    cap_out[2] += gnd
    
    # Decoupling capacitor
    cap_bypass = Component(
        symbol="Device:C",
        ref="C3", 
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    cap_bypass[1] += vcc_3v3
    cap_bypass[2] += gnd
    
    print("🚗 Adding motor control...")
    
    # Motor control nets (ESP32 GPIO outputs)
    motor1_a = Net('MOTOR1_A')
    motor1_b = Net('MOTOR1_B')
    motor2_a = Net('MOTOR2_A')
    motor2_b = Net('MOTOR2_B')
    
    # Connect ESP32 GPIOs to motor control
    esp32['IO25'] += motor1_a
    esp32['IO26'] += motor1_b  
    esp32['IO27'] += motor2_a
    esp32['IO14'] += motor2_b
    
    print("💡 Adding LED control...")
    
    # LED control net
    led_data = Net('LED_DATA')
    esp32['IO18'] += led_data
    
    # Status LED
    status_led = Component(
        symbol="Device:LED",
        ref="D1",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    status_resistor = Component(
        symbol="Device:R",
        ref="R1",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # LED circuit
    status_control = Net('STATUS_LED')
    esp32['IO2'] += status_control
    status_resistor[1] += status_control
    status_resistor[2] += status_led['A']
    status_led['K'] += gnd
    
    print("📡 Adding I2C for sensors...")
    
    # I2C bus for sensors
    i2c_sda = Net('I2C_SDA')
    i2c_scl = Net('I2C_SCL')
    
    esp32['IO21'] += i2c_sda
    esp32['IO22'] += i2c_scl
    
    print("🔊 Adding audio output...")
    
    # Audio output
    audio_out = Net('AUDIO_OUT')
    esp32['IO23'] += audio_out
    
    print("🔄 Adding reset circuit...")
    
    # Reset button
    reset_btn = Component(
        symbol="Switch:SW_Push",
        ref="SW1",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3"
    )
    
    # Reset pull-up resistor
    reset_pullup = Component(
        symbol="Device:R",
        ref="R2", 
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Reset circuit
    reset_net = Net('nRST')
    reset_pullup[1] += vcc_3v3
    reset_pullup[2] += reset_net
    reset_btn[1] += reset_net
    reset_btn[2] += gnd
    esp32['EN'] += reset_net
    
    print("✅ BB-8 Control Board created successfully!")
    print("")
    print("📋 Circuit Summary:")
    print("   • ESP32-WROOM-32 WiFi/Bluetooth microcontroller")
    print("   • 3.3V power regulation with AMS1117")
    print("   • Motor control outputs: IO25, IO26, IO27, IO14")
    print("   • I2C bus for sensors: IO21 (SDA), IO22 (SCL)")
    print("   • LED data output: IO18")
    print("   • Audio PWM output: IO23") 
    print("   • Status LED on IO2")
    print("   • Reset button and pull-up circuit")
    print("   • Power supply filtering capacitors")
    print("")
    print("🎯 Ready for BB-8 droid control!")
    

if __name__ == "__main__":
    print("🤖 Generating BB-8 Droid Control Board...")
    print("=" * 50)
    
    # Generate the circuit
    circuit = bb8_working()
    
    print("")
    print("🔌 Generating KiCad project files...")
    circuit.generate_kicad_project("BB8_Control_Board")
    
    print("")
    print("✅ BB-8 Control Board generated successfully!")
    print("📁 Project files created in: BB8_Control_Board/")
    print("")
    print("📋 Generated files:")
    print("   • BB8_Control_Board.kicad_pro - Project file")
    print("   • BB8_Control_Board.kicad_sch - Schematic") 
    print("   • BB8_Control_Board.kicad_pcb - PCB layout")
    print("   • BB8_Control_Board.net - Netlist")
    print("")
    print("🎯 Your BB-8 droid control board is ready!")
    print("💡 Connect external motor drivers, IMU, LEDs, and audio amp")
    print("🔋 Power the board with 5V supply")