#!/usr/bin/env python3
"""
ESP32 + IMU + USB-C Complete Circuit Tutorial
===========================================

This tutorial demonstrates how to design a complete circuit using circuit-synth
with ESP32 microcontroller, IMU sensor, and USB-C connector.

Features:
- ESP32-S3-MINI-1 module (WiFi/Bluetooth capable)
- MPU-6050 6-axis IMU (accelerometer + gyroscope)
- USB-C connector for power and data
- 3.3V voltage regulation from USB 5V
- I2C communication between ESP32 and IMU
- Reset and boot circuitry
- Proper decoupling capacitors

Component Selection Rationale:
------------------------------
1. ESP32-S3-MINI-1: Popular module with excellent KiCad symbol support
2. MPU-6050: Widely available, I2C interface, good KiCad symbol
3. USB_C_Receptacle_USB2.0_16P: Standard USB-C for power and data
4. AMS1117-3.3: Reliable 3.3V regulator, good footprint options
"""

from circuit_synth import *
from circuit_synth.annotations import enable_comments, TextBox, Table


@enable_comments
def create_power_supply():
    """
    USB-C to 3.3V Power Supply Circuit
    
    Converts USB 5V to 3.3V using AMS1117-3.3 linear regulator.
    Input: 5V from USB-C VBUS
    Output: 3.3V @ up to 800mA
    Dropout voltage: ~1.2V
    """
    # USB-C connector for power and data
    usb_conn = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P",
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
        value="USB-C"
    )
    
    # 3.3V voltage regulator
    vreg = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
        value="AMS1117-3.3"
    )
    
    # Input capacitor (USB 5V rail)
    cap_in = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Output capacitor (3.3V rail)
    cap_out = Component(
        symbol="Device:C", 
        ref="C",
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Power nets
    USB_5V = Net('USB_5V')    # 5V from USB
    VCC_3V3 = Net('VCC_3V3')  # Regulated 3.3V output
    GND = Net('GND')          # Ground reference
    
    # USB connector power connections
    usb_conn["VBUS"] += USB_5V
    usb_conn["GND_A5"] += GND
    usb_conn["GND_A12"] += GND 
    usb_conn["GND_B5"] += GND
    usb_conn["GND_B12"] += GND
    
    # Voltage regulator connections
    vreg["VI"] += USB_5V     # 5V input
    vreg["VO"] += VCC_3V3    # 3.3V output  
    vreg["GND"] += GND       # Ground
    
    # Input capacitor (5V side)
    cap_in[1] += USB_5V
    cap_in[2] += GND
    
    # Output capacitor (3.3V side)
    cap_out[1] += VCC_3V3
    cap_out[2] += GND
    
    return usb_conn, vreg, cap_in, cap_out, USB_5V, VCC_3V3, GND


@enable_comments  
def create_esp32_module():
    """
    ESP32-S3-MINI-1 Microcontroller Module
    
    WiFi and Bluetooth enabled microcontroller with:
    - 32-bit dual-core Xtensa LX7 processor
    - 320KB SRAM, 8MB Flash
    - WiFi 802.11 b/g/n, Bluetooth 5.0
    - Multiple I2C, SPI, UART interfaces
    - Built-in antenna
    """
    esp32 = Component(
        symbol="RF_Module:ESP32-S3-MINI-1",
        ref="U",
        footprint="RF_Module:ESP32-S3-MINI-1",
        value="ESP32-S3-MINI-1"
    )
    
    # Decoupling capacitors for ESP32
    cap_esp1 = Component(
        symbol="Device:C",
        ref="C", 
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    cap_esp2 = Component(
        symbol="Device:C",
        ref="C",
        value="10uF", 
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    return esp32, cap_esp1, cap_esp2


@enable_comments
def create_imu_sensor():
    """
    MPU-6050 6-Axis IMU Sensor
    
    Integrated 6-axis MotionTracking device:
    - 3-axis gyroscope with ±250, ±500, ±1000, ±2000°/sec ranges
    - 3-axis accelerometer with ±2g, ±4g, ±8g, ±16g ranges
    - I2C interface (address 0x68 or 0x69)
    - Built-in 16-bit ADCs and programmable digital filters
    - Operating voltage: 2.375V to 3.46V
    """
    imu = Component(
        symbol="Sensor_Motion:MPU-6050",
        ref="U",
        footprint="Sensor_Motion:InvenSense_QFN-24_4x4mm_P0.5mm",
        value="MPU-6050"
    )
    
    # I2C pull-up resistors (required for I2C communication)
    r_sda_pullup = Component(
        symbol="Device:R",
        ref="R",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    r_scl_pullup = Component(
        symbol="Device:R", 
        ref="R",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # IMU decoupling capacitor
    cap_imu = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    return imu, r_sda_pullup, r_scl_pullup, cap_imu


@enable_comments
def create_reset_boot_circuit():
    """
    ESP32 Reset and Boot Control Circuit
    
    Provides manual reset capability and boot mode selection:
    - Reset button pulls EN (enable) pin low
    - Boot button (GPIO0) for programming mode entry
    - Pull-up resistors ensure proper default states
    """
    # Reset button (momentary, normally open)
    btn_reset = Component(
        symbol="Switch:SW_Push",
        ref="SW",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3",
        value="RESET"
    )
    
    # Boot button (GPIO0 for programming mode)
    btn_boot = Component(
        symbol="Switch:SW_Push", 
        ref="SW",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3",
        value="BOOT"
    )
    
    # Pull-up resistor for EN pin
    r_en_pullup = Component(
        symbol="Device:R",
        ref="R", 
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Pull-up resistor for GPIO0
    r_gpio0_pullup = Component(
        symbol="Device:R",
        ref="R",
        value="10k", 
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    return btn_reset, btn_boot, r_en_pullup, r_gpio0_pullup


@circuit(name="ESP32_IMU_USBC_Complete")
def esp32_imu_usbc_circuit():
    """
    Complete ESP32 + IMU + USB-C Development Board
    
    This circuit combines all subsystems into a functional development board:
    - Power management: USB-C 5V to 3.3V regulation
    - Microcontroller: ESP32-S3-MINI-1 with WiFi/Bluetooth
    - Motion sensing: MPU-6050 6-axis IMU via I2C
    - Programming: USB-C data connection and reset/boot buttons
    - Proper decoupling and pull-up resistors throughout
    """
    
    # Create all subcircuits
    usb_conn, vreg, cap_in, cap_out, USB_5V, VCC_3V3, GND = create_power_supply()
    esp32, cap_esp1, cap_esp2 = create_esp32_module()
    imu, r_sda_pullup, r_scl_pullup, cap_imu = create_imu_sensor()
    btn_reset, btn_boot, r_en_pullup, r_gpio0_pullup = create_reset_boot_circuit()
    
    # I2C communication nets
    I2C_SDA = Net('I2C_SDA')
    I2C_SCL = Net('I2C_SCL') 
    
    # USB data nets
    USB_DP = Net('USB_DP')
    USB_DM = Net('USB_DM')
    
    # Control signal nets
    ESP32_EN = Net('ESP32_EN')
    ESP32_GPIO0 = Net('ESP32_GPIO0')
    
    # ESP32 power connections
    esp32["VDD"] += VCC_3V3
    esp32["GND"] += GND
    
    # ESP32 decoupling capacitors
    cap_esp1[1] += VCC_3V3
    cap_esp1[2] += GND
    cap_esp2[1] += VCC_3V3  
    cap_esp2[2] += GND
    
    # ESP32 I2C connections (using GPIO21=SDA, GPIO22=SCL)
    esp32["GPIO21"] += I2C_SDA
    esp32["GPIO22"] += I2C_SCL
    
    # ESP32 USB connections for programming
    esp32["GPIO19"] += USB_DM  # USB D- data line
    esp32["GPIO20"] += USB_DP  # USB D+ data line
    
    # ESP32 control pins
    esp32["EN"] += ESP32_EN
    esp32["GPIO0"] += ESP32_GPIO0
    
    # USB data connections
    usb_conn["DP1"] += USB_DP
    usb_conn["DN1"] += USB_DM
    usb_conn["DP2"] += USB_DP  # USB-C is reversible 
    usb_conn["DN2"] += USB_DM
    
    # IMU power and I2C connections  
    imu["VCC"] += VCC_3V3
    imu["GND"] += GND
    imu["SDA"] += I2C_SDA
    imu["SCL"] += I2C_SCL
    
    # IMU address pin (connect to GND for address 0x68)
    imu["AD0"] += GND
    
    # IMU decoupling capacitor
    cap_imu[1] += VCC_3V3
    cap_imu[2] += GND
    
    # I2C pull-up resistors
    r_sda_pullup[1] += VCC_3V3
    r_sda_pullup[2] += I2C_SDA
    r_scl_pullup[1] += VCC_3V3
    r_scl_pullup[2] += I2C_SCL
    
    # Reset button circuit
    btn_reset[1] += ESP32_EN
    btn_reset[2] += GND
    r_en_pullup[1] += VCC_3V3
    r_en_pullup[2] += ESP32_EN
    
    # Boot button circuit (GPIO0)
    btn_boot[1] += ESP32_GPIO0
    btn_boot[2] += GND  
    r_gpio0_pullup[1] += VCC_3V3
    r_gpio0_pullup[2] += ESP32_GPIO0
    
    # Create design annotations
    annotations = [
        TextBox(
            text="Power Supply: USB-C 5V → 3.3V via AMS1117",
            position=(10, 10),
            size=(60, 10),
            style="title"
        ),
        TextBox(
            text="I2C Communication: ESP32 ↔ MPU-6050 IMU",
            position=(10, 25),
            size=(60, 10), 
            style="note"
        ),
        Table(
            headers=["Component", "Function", "Interface"],
            rows=[
                ["ESP32-S3-MINI-1", "Microcontroller", "WiFi/BT, GPIO"],
                ["MPU-6050", "6-axis IMU", "I2C (0x68)"],
                ["USB-C", "Power & Data", "5V power, USB 2.0"],
                ["AMS1117-3.3", "Voltage Regulator", "5V → 3.3V"]
            ],
            position=(100, 20),
            title="System Components"
        )
    ]
    
    return annotations


if __name__ == "__main__":
    print("ESP32 + IMU + USB-C Circuit Tutorial")
    print("=====================================")
    print()
    print("This tutorial creates a complete development board with:")
    print("• ESP32-S3-MINI-1 microcontroller module")
    print("• MPU-6050 6-axis IMU sensor")  
    print("• USB-C connector for power and programming")
    print("• 3.3V voltage regulation")
    print("• I2C communication interface")
    print("• Reset and boot control buttons")
    print()
    
    # Generate the circuit
    circuit = esp32_imu_usbc_circuit()
    
    print("Circuit generation completed!")
    print(f"Total components: {len(circuit.components)}")
    print(f"Total nets: {len(circuit.nets)}")
    print()
    print("Key connections:")
    print("• Power: USB-C VBUS → AMS1117 → 3.3V rail")
    print("• I2C: ESP32 GPIO21/22 ↔ MPU-6050 SDA/SCL")
    print("• USB: ESP32 GPIO19/20 ↔ USB-C D+/D-")
    print("• Control: Reset/Boot buttons with pull-ups")
    print()
    print("Ready for KiCad schematic generation!")