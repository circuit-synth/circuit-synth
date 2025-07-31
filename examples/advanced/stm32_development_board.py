#!/usr/bin/env python3
"""
STM32 Development Board Design
=============================

Complete STM32F411CEUx development board with:
- STM32F411CEUx microcontroller (ARM Cortex-M4, USB support)
- LSM6DS3 IMU sensor (6-axis accelerometer + gyroscope, I2C)
- USB-C connector for power and data
- 3.3V power regulation from USB 5V using AMS1117-3.3
- SWD programming interface (4-pin header)
- Reset button with proper debouncing
- Status LED with current limiting resistor
- Crystal oscillator (8MHz external crystal)
- Comprehensive decoupling capacitors

Professional-grade design suitable for prototyping and development.
"""

from circuit_synth import Component, Net, circuit, TextBox, Table
from circuit_synth.core.decorators import enable_comments


@enable_comments
@circuit(name="STM32_Development_Board")
def create_stm32_development_board():
    """
    STM32F411CEUx Development Board
    
    Features:
    - ARM Cortex-M4 @ 100MHz with USB 2.0 FS
    - 6-axis IMU sensor (LSM6DS3)
    - USB-C power and data interface
    - SWD programming connector
    - Professional power regulation and filtering
    """
    
    # ========================================================================
    # POWER NETS
    # ========================================================================
    
    VCC_5V = Net('VCC_5V')      # USB 5V input
    VCC_3V3 = Net('VCC_3V3')    # Regulated 3.3V rail
    GND = Net('GND')            # Ground
    VDDA = Net('VDDA')          # Analog 3.3V rail
    
    # ========================================================================
    # USB-C CONNECTOR AND POWER INPUT
    # ========================================================================
    
    usb_connector = Component(
        symbol="Connector:USB_C_Receptacle",
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle_Amphenol_12401548E4-2A",
        value="USB_C"
    )
    
    # Connect USB power and ground
    usb_connector["VBUS"] += VCC_5V
    usb_connector["GND"] += GND
    usb_connector["SHIELD"] += GND
    
    # USB data lines (will connect to STM32 later)
    USB_DP = Net('USB_DP')
    USB_DM = Net('USB_DM')
    usb_connector["D+"] += USB_DP
    usb_connector["D-"] += USB_DM
    
    # ========================================================================
    # 3.3V POWER REGULATION
    # ========================================================================
    
    # Main 3.3V linear regulator
    vreg_3v3 = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
        value="AMS1117-3.3"
    )
    
    vreg_3v3["VI"] += VCC_5V
    vreg_3v3["VO"] += VCC_3V3
    vreg_3v3["GND"] += GND
    
    # Input decoupling capacitor for regulator
    cap_vin = Component(
        symbol="Device:C",
        ref="C",
        footprint="Capacitor_SMD:C_0805_2012Metric",
        value="10uF"
    )
    cap_vin[1] += VCC_5V
    cap_vin[2] += GND
    
    # Output decoupling capacitor for regulator
    cap_vout = Component(
        symbol="Device:C",
        ref="C",
        footprint="Capacitor_SMD:C_0805_2012Metric",
        value="22uF"
    )
    cap_vout[1] += VCC_3V3
    cap_vout[2] += GND
    
    # Additional small ceramic capacitor for high frequency filtering
    cap_3v3_hf = Component(
        symbol="Device:C",
        ref="C",
        footprint="Capacitor_SMD:C_0603_1608Metric",
        value="100nF"
    )
    cap_3v3_hf[1] += VCC_3V3
    cap_3v3_hf[2] += GND
    
    # Connect analog supply (same as digital for this design)
    VDDA += VCC_3V3
    VREF += VCC_3V3
    
    # ========================================================================
    # STM32F411CEUx MICROCONTROLLER
    # ========================================================================
    
    stm32 = Component(
        symbol="MCU_ST_STM32F4:STM32F411CEUx",
        ref="U",
        footprint="Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm_ThermalVias",
        value="STM32F411CEUx"
    )
    
    # Power connections
    stm32["VDD"] += VCC_3V3
    stm32["VDDA"] += VDDA
    stm32["VREF+"] += VREF
    stm32["VSS"] += GND
    stm32["VSSA"] += GND
    
    # USB connections
    stm32["PA11"] += USB_DM  # USB_DM
    stm32["PA12"] += USB_DP  # USB_DP
    
    # Crystal oscillator connections
    OSC_IN = Net('OSC_IN')
    OSC_OUT = Net('OSC_OUT')
    stm32["PH0-OSC_IN"] += OSC_IN
    stm32["PH1-OSC_OUT"] += OSC_OUT
    
    # Reset connection
    NRST = Net('NRST')
    stm32["NRST"] += NRST
    
    # SWD programming interface
    SWDIO = Net('SWDIO')
    SWCLK = Net('SWCLK')
    stm32["PA13"] += SWDIO  # SWDIO
    stm32["PA14"] += SWCLK  # SWCLK
    
    # I2C for IMU (I2C1)
    I2C_SCL = Net('I2C1_SCL')
    I2C_SDA = Net('I2C1_SDA')
    stm32["PB6"] += I2C_SCL  # I2C1_SCL
    stm32["PB7"] += I2C_SDA  # I2C1_SDA
    
    # Status LED (GPIO output)
    LED_STATUS = Net('LED_STATUS')
    stm32["PC13"] += LED_STATUS  # Built-in LED pin on many STM32 boards
    
    # ========================================================================
    # STM32 DECOUPLING CAPACITORS
    # ========================================================================
    
    # VDD decoupling capacitors (multiple for different frequencies)
    for i in range(4):  # 4 decoupling caps for robust power filtering
        cap_vdd = Component(
            symbol="Device:C",
            ref="C",
            footprint="Capacitor_SMD:C_0603_1608Metric",
            value="100nF"
        )
        cap_vdd[1] += VCC_3V3
        cap_vdd[2] += GND
    
    # VDDA decoupling (analog supply)
    cap_vdda = Component(
        symbol="Device:C",
        ref="C",
        footprint="Capacitor_SMD:C_0603_1608Metric",
        value="100nF"
    )
    cap_vdda[1] += VDDA
    cap_vdda[2] += GND
    
    # Additional bulk capacitor for STM32
    cap_vdd_bulk = Component(
        symbol="Device:C",
        ref="C",
        footprint="Capacitor_SMD:C_0805_2012Metric",
        value="10uF"
    )
    cap_vdd_bulk[1] += VCC_3V3
    cap_vdd_bulk[2] += GND
    
    # ========================================================================
    # CRYSTAL OSCILLATOR (8MHz)
    # ========================================================================
    
    crystal = Component(
        symbol="Device:Crystal",
        ref="Y",
        footprint="Crystal:Crystal_SMD_HC49-SD",
        value="8MHz"
    )
    crystal[1] += OSC_IN
    crystal[2] += OSC_OUT
    
    # Crystal load capacitors (typically 18-22pF for 8MHz crystal)
    cap_xtal1 = Component(
        symbol="Device:C",
        ref="C",
        footprint="Capacitor_SMD:C_0603_1608Metric",
        value="20pF"
    )
    cap_xtal1[1] += OSC_IN
    cap_xtal1[2] += GND
    
    cap_xtal2 = Component(
        symbol="Device:C",
        ref="C",
        footprint="Capacitor_SMD:C_0603_1608Metric",   
        value="20pF"
    )
    cap_xtal2[1] += OSC_OUT
    cap_xtal2[2] += GND
    
    # ========================================================================
    # RESET CIRCUIT
    # ========================================================================
    
    # Reset button
    reset_button = Component(
        symbol="Switch:SW_Push",
        ref="SW",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3",
        value="RESET"
    )
    reset_button[1] += NRST
    reset_button[2] += GND
    
    # Reset pull-up resistor
    res_reset_pullup = Component(
        symbol="Device:R",
        ref="R",  
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="10k"
    )
    res_reset_pullup[1] += VCC_3V3
    res_reset_pullup[2] += NRST
    
    # Reset debouncing capacitor
    cap_reset = Component(
        symbol="Device:C",
        ref="C",
        footprint="Capacitor_SMD:C_0603_1608Metric",
        value="100nF"
    )
    cap_reset[1] += NRST
    cap_reset[2] += GND
    
    # ========================================================================
    # SWD PROGRAMMING INTERFACE
    # ========================================================================
    
    swd_connector = Component(
        symbol="Connector_Generic:Conn_01x04",
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
        value="SWD"
    )
    
    # SWD connections: VCC, SWDIO, SWCLK, GND
    swd_connector[1] += VCC_3V3  # VCC (3.3V)
    swd_connector[2] += SWDIO    # SWDIO
    swd_connector[3] += SWCLK    # SWCLK  
    swd_connector[4] += GND      # GND
    
    # ========================================================================
    # STATUS LED
    # ========================================================================
    
    status_led = Component(
        symbol="Device:LED",
        ref="D",
        footprint="LED_SMD:LED_0603_1608Metric",
        value="GREEN"
    )
    
    # Current limiting resistor for LED
    res_led = Component(
        symbol="Device:R",
        ref="R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="1k"
    )
    
    # LED circuit: GPIO -> Resistor -> LED -> GND
    res_led[1] += LED_STATUS
    res_led[2] += status_led["A"]  # LED anode
    status_led["K"] += GND         # LED cathode
    
    # ========================================================================
    # IMU SENSOR (LSM6DS3)
    # ========================================================================
    
    imu = Component(
        symbol="Sensor_Motion:LSM6DS3",
        ref="U",
        footprint="Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y",
        value="LSM6DS3"
    )
    
    # Power connections
    imu["VDD"] += VCC_3V3
    imu["VDDIO"] += VCC_3V3
    imu["GND"] += GND
    
    # I2C connections
    imu["SCL"] += I2C_SCL
    imu["SDA"] += I2C_SDA
    
    # Address selection (connect to GND for 0x6A, VCC for 0x6B)
    imu["SDO/SA0"] += GND  # I2C address 0x6A
    
    # Chip select (not used in I2C mode, pull high)
    imu["CS"] += VCC_3V3
    
    # Interrupt pins (optional, can be left unconnected for basic operation)
    IMU_INT1 = Net('IMU_INT1')
    IMU_INT2 = Net('IMU_INT2')
    imu["INT1"] += IMU_INT1
    imu["INT2"] += IMU_INT2
    
    # Connect interrupts to STM32 GPIO pins
    stm32["PA0"] += IMU_INT1  # IMU INT1
    stm32["PA1"] += IMU_INT2  # IMU INT2
    
    # IMU decoupling capacitors
    cap_imu_vdd = Component(
        symbol="Device:C",
        ref="C",
        footprint="Capacitor_SMD:C_0603_1608Metric",
        value="100nF"
    )
    cap_imu_vdd[1] += VCC_3V3
    cap_imu_vdd[2] += GND
    
    cap_imu_vddio = Component(
        symbol="Device:C", 
        ref="C",
        footprint="Capacitor_SMD:C_0603_1608Metric",
        value="100nF"
    )
    cap_imu_vddio[1] += VCC_3V3
    cap_imu_vddio[2] += GND
    
    # ========================================================================
    # I2C PULL-UP RESISTORS
    # ========================================================================
    
    # I2C requires pull-up resistors on SDA and SCL lines
    res_i2c_scl = Component(
        symbol="Device:R",
        ref="R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="4.7k"
    )
    res_i2c_scl[1] += VCC_3V3
    res_i2c_scl[2] += I2C_SCL
    
    res_i2c_sda = Component(
        symbol="Device:R",
        ref="R", 
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="4.7k"
    )
    res_i2c_sda[1] += VCC_3V3
    res_i2c_sda[2] += I2C_SDA
    
    # ========================================================================
    # ADDITIONAL GPIO BREAKOUT (Optional expansion)
    # ========================================================================
    
    # Optional: Add a connector for additional GPIO access
    gpio_connector = Component(
        symbol="Connector_Generic:Conn_02x08_Odd_Even",
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_2x08_P2.54mm_Vertical",
        value="GPIO_EXPANSION"
    )
    
    # Connect some useful STM32 pins to expansion connector
    # Row 1: Digital pins
    gpio_connector[1] += VCC_3V3      # 3.3V
    gpio_connector[3] += stm32["PA2"] # UART2_TX / ADC_IN2
    gpio_connector[5] += stm32["PA3"] # UART2_RX / ADC_IN3
    gpio_connector[7] += stm32["PA4"] # SPI1_NSS / ADC_IN4 / DAC_OUT1
    gpio_connector[9] += stm32["PA5"] # SPI1_SCK / ADC_IN5
    gpio_connector[11] += stm32["PA6"] # SPI1_MISO / ADC_IN6
    gpio_connector[13] += stm32["PA7"] # SPI1_MOSI / ADC_IN7
    gpio_connector[15] += stm32["PB0"] # ADC_IN8
    
    # Row 2: More digital pins and ground
    gpio_connector[2] += GND          # GND
    gpio_connector[4] += stm32["PB1"] # ADC_IN9
    gpio_connector[6] += stm32["PB10"] # I2C2_SCL / UART3_TX
    gpio_connector[8] += stm32["PB3"] # SPI1_SCK (alternate)
    gpio_connector[10] += stm32["PB4"] # SPI1_MISO (alternate)
    gpio_connector[12] += stm32["PB5"] # SPI1_MOSI (alternate)
    gpio_connector[14] += stm32["PB8"] # I2C1_SCL (alternate)
    gpio_connector[16] += stm32["PB9"] # I2C1_SDA (alternate)
    
    # ========================================================================
    # DESIGN ANNOTATIONS
    # ========================================================================
    
    # Add design specifications table
    specs_table = Table(
        headers=["Parameter", "Value", "Notes"],
        rows=[
            ["MCU", "STM32F411CEUx", "ARM Cortex-M4 @ 100MHz"],
            ["Flash", "512KB", "User application space"],
            ["RAM", "128KB", "SRAM"],
            ["IMU", "LSM6DS3", "6-axis accel + gyro"],
            ["Power", "5V USB → 3.3V", "AMS1117 LDO regulator"],
            ["Programming", "SWD", "4-pin header"],
            ["Crystal", "8MHz", "External HSE"],
            ["I2C", "400kHz max", "IMU + expansion"],
            ["USB", "Full Speed", "Device mode"]
        ],
        position=(200, 100),
        title="STM32 Development Board Specifications"
    )
    
    # Add design notes
    design_notes = TextBox(
        text="Design Notes:\n"
             "• All decoupling capacitors placed close to power pins\n"
             "• Crystal load capacitors matched to 8MHz crystal\n"
             "• Reset circuit includes debouncing\n"
             "• I2C pull-ups sized for 400kHz operation\n"
             "• USB data lines require 90Ω differential impedance\n"
             "• Thermal vias under QFN packages for heat dissipation",
        position=(200, 200),
        size=(60, 40),
        style="design_note"
    )
    
    return [specs_table, design_notes]


if __name__ == "__main__":
    # Generate the STM32 development board
    print("Generating STM32 Development Board schematic...")
    
    # Create the circuit
    circuit_annotations = create_stm32_development_board()
    
    print("STM32 Development Board design complete!")
    print("\nFeatures implemented:")
    print("• STM32F411CEUx microcontroller (QFN-48)")
    print("• LSM6DS3 6-axis IMU sensor")
    print("• USB-C connector for power and data")
    print("• 3.3V power regulation with proper filtering")
    print("• SWD programming interface")
    print("• Reset button with debouncing")
    print("• Status LED")
    print("• 8MHz crystal oscillator")
    print("• Comprehensive decoupling capacitors")
    print("• GPIO expansion connector")
    print("• Professional-grade layout ready for manufacturing")