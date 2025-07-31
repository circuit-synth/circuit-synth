#!/usr/bin/env python3
"""
STM32 Development Board with IMU and USB-C
==========================================

This example creates a complete STM32 development board featuring:
- STM32F407VGTx microcontroller (100-pin LQFP)
- MPU-6050 6-axis IMU (accelerometer + gyroscope)
- USB-C connector for programming and power
- 3.3V power regulation from USB 5V
- Decoupling capacitors and basic support circuitry
- I2C connection between STM32 and IMU

Features:
- USB 2.0 interface for programming/debugging
- I2C communication with IMU sensor
- 3.3V regulation with proper decoupling
- Crystal oscillator for precise timing
- Reset button and boot configuration
"""

from circuit_synth import *


@circuit(name="STM32_IMU_USBC_Board")
def create_stm32_imu_board():
    """
    Complete STM32 development board with IMU and USB-C connectivity.
    
    This design provides a solid foundation for motion-sensing applications
    with USB connectivity for programming and debugging.
    """
    
    # Power and ground nets
    VCC_5V = Net('VCC_5V')      # USB 5V input
    VCC_3V3 = Net('VCC_3V3')    # Regulated 3.3V rail
    GND = Net('GND')            # Ground reference
    
    # Communication nets
    USB_DP = Net('USB_DP')      # USB D+ data line
    USB_DM = Net('USB_DM')      # USB D- data line
    I2C_SCL = Net('I2C_SCL')    # I2C clock to IMU
    I2C_SDA = Net('I2C_SDA')    # I2C data to IMU
    
    # Control and timing nets
    RESET = Net('RESET')        # MCU reset signal
    BOOT0 = Net('BOOT0')        # Boot mode selection
    OSC_IN = Net('OSC_IN')      # Crystal input
    OSC_OUT = Net('OSC_OUT')    # Crystal output
    
    # === USB-C Connector ===
    usb_connector = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P",
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12"
    )
    
    # Connect USB power and data
    usb_connector["VBUS"] += VCC_5V
    usb_connector["GND"] += GND
    usb_connector["SHIELD"] += GND
    usb_connector["D+"] += USB_DP
    usb_connector["D-"] += USB_DM
    
    # === STM32F407VGTx Microcontroller ===
    mcu = Component(
        symbol="MCU_ST_STM32F4:STM32F407VGTx",
        ref="U",
        footprint="Package_QFP:LQFP-100_14x14mm_P0.5mm"
    )
    
    # Power connections
    mcu["VDD"] += VCC_3V3      # Main power
    mcu["VDDA"] += VCC_3V3     # Analog power
    mcu["VBAT"] += VCC_3V3     # Backup power
    
    mcu["VSS"] += GND          # Main ground
    mcu["VSSA"] += GND         # Analog ground
    
    # USB connections
    mcu["PA11"] += USB_DM      # USB D-
    mcu["PA12"] += USB_DP      # USB D+
    
    # I2C connections for IMU
    mcu["PB6"] += I2C_SCL      # I2C1_SCL
    mcu["PB7"] += I2C_SDA      # I2C1_SDA
    
    # Crystal oscillator connections
    mcu["PH0"] += OSC_IN       # HSE_IN
    mcu["PH1"] += OSC_OUT      # HSE_OUT
    
    # Reset and boot pins
    mcu["NRST"] += RESET
    mcu["BOOT0"] += BOOT0
    
    # === 3.3V Voltage Regulator ===
    voltage_regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    voltage_regulator["VI"] += VCC_5V
    voltage_regulator["VO"] += VCC_3V3  
    voltage_regulator["GND"] += GND
    
    # === MPU-6050 IMU Sensor ===
    imu = Component(
        symbol="Sensor_Motion:MPU-6050",
        ref="U",
        footprint="Package_LGA:LGA-24_3x3mm_P0.43mm"
    )
    
    # Power connections
    imu["VDD"] += VCC_3V3
    imu["GND"] += GND
    imu["VLOGIC"] += VCC_3V3   # Logic level reference
    
    # I2C connections
    imu["SCL"] += I2C_SCL
    imu["SDA"] += I2C_SDA
    
    # Address selection (tied to ground for 0x68)
    imu["AD0"] += GND
    
    # === Crystal Oscillator (8MHz for STM32F4) ===
    crystal = Component(
        symbol="Device:Crystal",
        ref="Y",
        value="8MHz",
        footprint="Crystal:Crystal_SMD_HC49-SD_H1.5mm"
    )
    
    crystal[1] += OSC_IN
    crystal[2] += OSC_OUT
    
    # Crystal load capacitors
    cap_xtal1 = Component(
        symbol="Device:C",
        ref="C",
        value="22pF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    cap_xtal2 = Component(
        symbol="Device:C", 
        ref="C",
        value="22pF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    cap_xtal1[1] += OSC_IN
    cap_xtal1[2] += GND
    cap_xtal2[1] += OSC_OUT
    cap_xtal2[2] += GND
    
    # === Reset Button ===
    reset_button = Component(
        symbol="Switch:SW_Push",
        ref="SW",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3"
    )
    
    reset_button[1] += RESET
    reset_button[2] += GND
    
    # Reset pull-up resistor
    reset_pullup = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    reset_pullup[1] += VCC_3V3
    reset_pullup[2] += RESET
    
    # === Boot Configuration ===
    # Boot0 pull-down for normal operation
    boot0_pulldown = Component(
        symbol="Device:R",
        ref="R", 
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    boot0_pulldown[1] += BOOT0
    boot0_pulldown[2] += GND
    
    # === I2C Pull-up Resistors ===
    i2c_scl_pullup = Component(
        symbol="Device:R",
        ref="R",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    i2c_sda_pullup = Component(
        symbol="Device:R",
        ref="R",
        value="4.7k", 
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    i2c_scl_pullup[1] += VCC_3V3
    i2c_scl_pullup[2] += I2C_SCL
    i2c_sda_pullup[1] += VCC_3V3
    i2c_sda_pullup[2] += I2C_SDA
    
    # === Power Supply Decoupling Capacitors ===
    
    # Voltage regulator input/output capacitors
    reg_input_cap = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    reg_output_cap = Component(
        symbol="Device:C",
        ref="C", 
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    reg_input_cap[1] += VCC_5V
    reg_input_cap[2] += GND
    reg_output_cap[1] += VCC_3V3
    reg_output_cap[2] += GND
    
    # MCU power decoupling capacitors
    mcu_caps = []
    for i in range(6):  # Multiple 100nF caps for MCU power pins
        cap = Component(
            symbol="Device:C", 
            ref="C",
            value="100nF",
            footprint="Capacitor_SMD:C_0603_1608Metric"
        )
        cap[1] += VCC_3V3
        cap[2] += GND
        mcu_caps.append(cap)
    
    # Additional bulk capacitor for MCU
    mcu_bulk_cap = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    mcu_bulk_cap[1] += VCC_3V3
    mcu_bulk_cap[2] += GND
    
    # IMU decoupling capacitor
    imu_cap = Component(
        symbol="Device:C",
        ref="C",
        value="100nF", 
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    imu_cap[1] += VCC_3V3
    imu_cap[2] += GND
    
    # === Status LED ===
    status_led = Component(
        symbol="Device:LED",
        ref="D",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    led_resistor = Component(
        symbol="Device:R",
        ref="R",
        value="330",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Connect LED to GPIO pin (PC13 is common for status LEDs)
    mcu["PC13"] += led_resistor[1]
    led_resistor[2] += status_led[1]  # Anode
    status_led[2] += GND             # Cathode
    
    return circuit


if __name__ == "__main__":
    # Generate the circuit
    design = create_stm32_imu_board()
    
    # Generate text netlist
    print("=== Text Netlist ===")
    print(design.generate_full_netlist())
    
    # Generate KiCad project files
    try:
        print("\n=== Generating KiCad Project ===")
        design.generate_kicad_project("stm32_imu_board")
        print("✅ KiCad project generated successfully!")
        print("📁 Project files saved to: ./output/stm32_imu_board/")
        
    except Exception as e:
        print(f"❌ Error generating KiCad project: {e}")
        
    print("\n=== Circuit Summary ===")
    print("🔌 USB-C connector for power and programming")  
    print("🧠 STM32F407VGTx microcontroller (Cortex-M4)")
    print("📱 MPU-6050 6-axis IMU sensor")
    print("⚡ 3.3V power regulation from USB 5V")
    print("🔄 I2C communication interface")
    print("💎 8MHz crystal oscillator")
    print("🔴 Status LED on PC13")
    print("🔄 Reset button and boot configuration")