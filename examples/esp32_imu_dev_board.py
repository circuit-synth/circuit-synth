#!/usr/bin/env python3
"""
ESP32 Development Board with IMU and USB-C

This script generates a complete ESP32 development board featuring:
- ESP32-S3 microcontroller
- MPU-6050 IMU sensor with I2C interface
- USB-C connector for power and programming
- Power management with 3.3V regulation
- Programming interface with auto-reset circuitry
- Status LEDs and GPIO breakout
"""

import sys
import os
import json

# Add the src directory to the path so we can import circuit_synth
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from circuit_synth import Circuit, Component, Net, circuit
from circuit_synth.kicad.unified_kicad_integration import create_unified_kicad_integration

@circuit(name="ESP32_IMU_Dev_Board")
def create_esp32_imu_dev_board():
    """
    ESP32 Development Board with IMU and USB-C
    
    Features:
    - ESP32-S3 with WiFi/Bluetooth
    - MPU-6050 6-axis IMU sensor
    - USB-C for power and programming
    - 3.3V power regulation
    - Auto-reset programming circuit
    - Status LEDs and GPIO breakout
    """
    
    # Define power and ground nets
    VCC_5V = Net('VCC_5V')
    VCC_3V3 = Net('VCC_3V3')
    VCC_1V8 = Net('VCC_1V8')  # Internal 1.8V for ESP32
    GND = Net('GND')
    
    # Define important signal nets
    USB_DP = Net('USB_DP')
    USB_DM = Net('USB_DM')
    I2C_SDA = Net('I2C_SDA')
    I2C_SCL = Net('I2C_SCL')
    UART_TX = Net('UART_TX')
    UART_RX = Net('UART_RX')
    ESP_EN = Net('ESP_EN')
    ESP_IO0 = Net('ESP_IO0')
    
    # ===== USB-C CONNECTOR =====
    usb_c = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P",
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
        value="USB-C"
    )
    
    # Connect USB-C power and data
    usb_c["VBUS"] += VCC_5V
    usb_c["GND"] += GND
    usb_c["SHIELD"] += GND
    usb_c["D+"] += USB_DP
    usb_c["D-"] += USB_DM
    
    
    # ===== POWER MANAGEMENT =====
    
    # Input protection and filtering
    fuse = Component(
        symbol="Device:Fuse",
        ref="F",
        footprint="Fuse:Fuse_0603_1608Metric",
        value="500mA"
    )
    fuse[1] += VCC_5V
    fuse[2] += Net('VCC_5V_FUSED')
    
    
    # Input capacitor
    c_in = Component(
        symbol="Device:C",
        ref="C",
        footprint="Capacitor_SMD:C_0805_2012Metric",
        value="10uF"
    )
    c_in[1] += Net('VCC_5V_FUSED')
    c_in[2] += GND
    
    
    # 3.3V Linear regulator
    vreg_3v3 = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
        value="AMS1117-3.3"
    )
    vreg_3v3["VI"] += Net('VCC_5V_FUSED')
    vreg_3v3["VO"] += VCC_3V3
    vreg_3v3["GND"] += GND
    
    
    # 3.3V output capacitor
    c_3v3 = Component(
        symbol="Device:C",
        ref="C",
        footprint="Capacitor_SMD:C_0805_2012Metric",
        value="22uF"
    )
    c_3v3[1] += VCC_3V3
    c_3v3[2] += GND
    
    
    # ===== ESP32-S3 MICROCONTROLLER =====
    esp32 = Component(
        symbol="MCU_Espressif:ESP32-S3",
        ref="U",
        footprint="Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP5.6x5.6mm",
        value="ESP32-S3"
    )
    
    # Power connections
    esp32["VDD3P3_RTC"] += VCC_3V3
    esp32["VDD3P3_CPU"] += VCC_3V3
    esp32["VDD_SPI"] += VCC_3V3
    esp32["VDD3P3"] += VCC_3V3
    esp32["VDDA"] += VCC_3V3
    esp32["GND"] += GND
    esp32["EP"] += GND  # Exposed pad
    
    # USB interface (built-in USB-Serial)
    esp32["GPIO19"] += USB_DM
    esp32["GPIO20"] += USB_DP
    
    # I2C for IMU
    esp32["GPIO21"] += I2C_SDA
    esp32["GPIO22"] += I2C_SCL
    
    # UART interface (for programming)
    esp32["GPIO43"] += UART_TX
    esp32["GPIO44"] += UART_RX
    
    # Control signals
    esp32["EN"] += ESP_EN
    esp32["GPIO0"] += ESP_IO0
    
    
    
    # ESP32 bypass capacitors
    for i in range(4):
        cap = Component(
            symbol="Device:C",
            ref="C",
            footprint="Capacitor_SMD:C_0402_1005Metric",
            value="100nF"
        )
        cap[1] += VCC_3V3
        cap[2] += GND
        
    
    # ===== IMU SENSOR (MPU-6050) =====
    imu = Component(
        symbol="Sensor_Motion:MPU-6050",
        ref="U",
        footprint="Sensor_Motion:InvenSense_QFN-24_4x4mm_P0.5mm",
        value="MPU-6050"
    )
    
    # Power and ground
    imu["VDD"] += VCC_3V3
    imu["VLOGIC"] += VCC_3V3
    imu["GND"] += GND
    
    # I2C interface
    imu["SDA"] += I2C_SDA
    imu["SCL"] += I2C_SCL
    
    # Address pin (connect to GND for default address)
    imu["AD0"] += GND
    
    # Interrupt pin (optional)
    imu["INT"] += Net('IMU_INT')
    esp32["GPIO23"] += Net('IMU_INT')
    
    
    
    # IMU bypass capacitors
    c_imu1 = Component(
        symbol="Device:C",
        ref="C",
        footprint="Capacitor_SMD:C_0402_1005Metric",
        value="100nF"
    )
    c_imu1[1] += VCC_3V3
    c_imu1[2] += GND
    
    
    c_imu2 = Component(
        symbol="Device:C",
        ref="C",
        footprint="Capacitor_SMD:C_0402_1005Metric",
        value="10nF"
    )
    c_imu2[1] += VCC_3V3
    c_imu2[2] += GND
    
    
    # ===== I2C PULL-UP RESISTORS =====
    r_sda = Component(
        symbol="Device:R",
        ref="R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="4.7k"
    )
    r_sda[1] += VCC_3V3
    r_sda[2] += I2C_SDA
    
    
    r_scl = Component(
        symbol="Device:R",
        ref="R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="4.7k"
    )
    r_scl[1] += VCC_3V3
    r_scl[2] += I2C_SCL
    
    
    # ===== PROGRAMMING AND RESET CIRCUIT =====
    
    # Enable pullup resistor
    r_en = Component(
        symbol="Device:R",
        ref="R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="10k"
    )
    r_en[1] += VCC_3V3
    r_en[2] += ESP_EN
    
    
    # IO0 pullup resistor (for normal operation)
    r_io0 = Component(
        symbol="Device:R",
        ref="R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="10k"
    )
    r_io0[1] += VCC_3V3
    r_io0[2] += ESP_IO0
    
    
    # Reset button
    btn_reset = Component(
        symbol="Switch:SW_Push",
        ref="SW",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3",
        value="RESET"
    )
    btn_reset[1] += ESP_EN
    btn_reset[2] += GND
    
    
    # Boot button (IO0)
    btn_boot = Component(
        symbol="Switch:SW_Push",
        ref="SW",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3",
        value="BOOT"
    )
    btn_boot[1] += ESP_IO0
    btn_boot[2] += GND
    
    
    # Auto-reset circuit capacitors
    c_reset = Component(
        symbol="Device:C",
        ref="C",
        footprint="Capacitor_SMD:C_0603_1608Metric",
        value="100nF"
    )
    c_reset[1] += UART_RX  # DTR signal from USB-serial converter
    c_reset[2] += ESP_EN
    
    
    c_boot = Component(
        symbol="Device:C",
        ref="C",
        footprint="Capacitor_SMD:C_0603_1608Metric",
        value="100nF"
    )
    c_boot[1] += UART_TX  # RTS signal from USB-serial converter
    c_boot[2] += ESP_IO0
    
    
    # ===== STATUS LEDS =====
    
    # Power LED
    led_power = Component(
        symbol="Device:LED",
        ref="D",
        footprint="LED_SMD:LED_0603_1608Metric",
        value="PWR_LED"
    )
    
    r_led_power = Component(
        symbol="Device:R",
        ref="R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="1k"
    )
    
    r_led_power[1] += VCC_3V3
    r_led_power[2] += led_power["A"]
    led_power["K"] += GND
    
    
    
    
    # User LED (connected to GPIO2)
    led_user = Component(
        symbol="Device:LED",
        ref="D",
        footprint="LED_SMD:LED_0603_1608Metric",
        value="USER_LED"
    )
    
    r_led_user = Component(
        symbol="Device:R",
        ref="R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="470"
    )
    
    esp32["GPIO2"] += r_led_user[1]
    r_led_user[2] += led_user["A"]
    led_user["K"] += GND
    
    
    
    
    # ===== GPIO BREAKOUT HEADERS =====
    
    # Main GPIO header (2x20 pins)
    gpio_header = Component(
        symbol="Connector_Generic:Conn_02x20_Odd_Even",
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical",
        value="GPIO_HEADER"
    )
    
    # Connect some key GPIO pins
    gpio_header[1] += VCC_3V3      # Pin 1
    gpio_header[2] += VCC_5V       # Pin 2
    gpio_header[3] += esp32["GPIO4"]   # Pin 3
    gpio_header[4] += VCC_5V       # Pin 4
    gpio_header[5] += esp32["GPIO5"]   # Pin 5
    gpio_header[6] += GND          # Pin 6
    gpio_header[7] += esp32["GPIO6"]   # Pin 7
    gpio_header[8] += esp32["GPIO7"]   # Pin 8
    gpio_header[9] += GND          # Pin 9
    gpio_header[10] += esp32["GPIO8"]  # Pin 10
    gpio_header[11] += esp32["GPIO9"]  # Pin 11
    gpio_header[12] += esp32["GPIO10"] # Pin 12
    gpio_header[13] += esp32["GPIO11"] # Pin 13
    gpio_header[14] += GND         # Pin 14
    gpio_header[15] += esp32["GPIO12"] # Pin 15
    gpio_header[16] += esp32["GPIO13"] # Pin 16
    gpio_header[17] += VCC_3V3     # Pin 17
    gpio_header[18] += esp32["GPIO14"] # Pin 18
    gpio_header[19] += esp32["GPIO15"] # Pin 19
    gpio_header[20] += GND         # Pin 20
    
    # Continue with remaining pins
    gpio_header[21] += esp32["GPIO16"] # Pin 21
    gpio_header[22] += esp32["GPIO17"] # Pin 22
    gpio_header[23] += esp32["GPIO18"] # Pin 23
    gpio_header[24] += esp32["GPIO19"] # Pin 24 (USB D-)
    gpio_header[25] += GND         # Pin 25
    gpio_header[26] += esp32["GPIO20"] # Pin 26 (USB D+)
    gpio_header[27] += I2C_SDA     # Pin 27 (GPIO21)
    gpio_header[28] += I2C_SCL     # Pin 28 (GPIO22)
    gpio_header[29] += esp32["GPIO23"] # Pin 29 (IMU INT)
    gpio_header[30] += GND         # Pin 30
    
    # Add remaining pins for SPI, ADC, etc.
    gpio_header[31] += esp32["GPIO35"] # Pin 31 (ADC)
    gpio_header[32] += esp32["GPIO36"] # Pin 32 (ADC)
    gpio_header[33] += esp32["GPIO37"] # Pin 33 (ADC)
    gpio_header[34] += esp32["GPIO38"] # Pin 34 (ADC)
    gpio_header[35] += esp32["GPIO39"] # Pin 35 (ADC)
    gpio_header[36] += esp32["GPIO40"] # Pin 36 (ADC)
    gpio_header[37] += esp32["GPIO41"] # Pin 37
    gpio_header[38] += esp32["GPIO42"] # Pin 38
    gpio_header[39] += UART_TX     # Pin 39 (GPIO43)
    gpio_header[40] += UART_RX     # Pin 40 (GPIO44)
    
    
def main():
    """Generate the ESP32 IMU development board and create KiCad project files."""
    print("Generating ESP32 IMU Development Board...")
    
    # Create the circuit
    circuit = create_esp32_imu_dev_board()
    
    # Define project parameters
    project_name = "ESP32_IMU_Dev_Board"
    output_dir = os.path.join(os.path.dirname(__file__), "..", "generated_projects", project_name)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate netlists
    print("\n=== Text Netlist ===")
    text_netlist = circuit.to_netlist()
    print(text_netlist)
    
    # Save text netlist
    with open(os.path.join(output_dir, f"{project_name}.net"), 'w') as f:
        f.write(text_netlist)
    
    print("\n=== JSON Netlist ===")
    json_netlist = circuit.to_json()
    print(json_netlist)
    
    # Save JSON netlist
    with open(os.path.join(output_dir, f"{project_name}.json"), 'w') as f:
        f.write(json_netlist)
    
    # Generate KiCad project
    print(f"\n=== Generating KiCad Project in {output_dir} ===")
    try:
        # Create unified KiCad integration
        kicad_integration = create_unified_kicad_integration(
            output_dir=output_dir,
            project_name=project_name
        )
        
        # Convert circuit to circuit data format
        circuit_data = json.loads(circuit.to_json())
        
        # Generate schematic
        schematic_generator = kicad_integration.get_schematic_generator()
        result = schematic_generator.generate_from_circuit_data(circuit_data)
        
        print("KiCad project generated successfully!")
        print(f"Generated files in: {output_dir}")
        
    except Exception as e:
        print(f"Error generating KiCad project: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print(f"\nProject files saved to: {output_dir}")
    print("\nTo open in KiCad:")
    print(f"  kicad {os.path.join(output_dir, project_name + '.kicad_pro')}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())