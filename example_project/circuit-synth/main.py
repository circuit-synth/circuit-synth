#!/usr/bin/env python3
"""
ESP32-C6 Development Board - Circuit-Synth Example
===================================================

This is a complete, production-ready ESP32-C6 development board design
demonstrating hierarchical circuit architecture with circuit-synth.

Features:
- ESP32-C6-MINI-1 module (WiFi 6, Bluetooth 5, Thread, Zigbee)
- USB-C power and programming interface  
- 3.3V power regulation with proper decoupling
- Status LED with current limiting
- Reset button and boot mode selection
- Debug interface for professional development

Run this file to generate the complete KiCad project!
"""

from circuit_synth import Component, Net, circuit

# Import hierarchical subcircuits
from usb import usb_subcircuit
from power_supply import power_supply_subcircuit  
from led_blinker import led_blinker_subcircuit
from esp32c6 import esp32c6_subcircuit


@circuit(name="ESP32_C6_Development_Board")
def esp32_c6_dev_board():
    """
    Main ESP32-C6 development board circuit
    
    This is the top-level circuit that defines the shared nets
    and connects all the hierarchical subcircuits together.
    """
    
    # Define shared power and ground nets
    vcc_5v = Net('VCC_5V')      # USB 5V power
    vcc_3v3 = Net('VCC_3V3')    # Regulated 3.3V power  
    gnd = Net('GND')            # System ground
    
    # USB data and control nets
    usb_dp = Net('USB_DP')      # USB D+ data line
    usb_dm = Net('USB_DM')      # USB D- data line
    usb_vbus = Net('USB_VBUS')  # USB bus voltage detection
    
    # ESP32-C6 programming and debug nets
    esp32_tx = Net('ESP32_TX')   # UART transmit for programming
    esp32_rx = Net('ESP32_RX')   # UART receive for programming  
    esp32_en = Net('ESP32_EN')   # ESP32 enable/reset control
    esp32_io0 = Net('ESP32_IO0') # Boot mode control (GPIO0)
    
    # Status LED control
    led_control = Net('LED_CTRL') # GPIO pin controlling status LED
    
    # Create hierarchical subcircuits
    # Each subcircuit handles a specific functional area
    
    # USB-C connector with ESD protection and CC resistors
    usb_circuit = usb_subcircuit(
        vbus_net=usb_vbus,
        vcc_5v_net=vcc_5v, 
        gnd_net=gnd,
        usb_dp_net=usb_dp,
        usb_dm_net=usb_dm
    )
    
    # 5V to 3.3V power regulation with proper decoupling
    power_circuit = power_supply_subcircuit(
        vin_net=vcc_5v,
        vout_net=vcc_3v3,
        gnd_net=gnd
    )
    
    # ESP32-C6 microcontroller with crystal and decoupling
    esp32_circuit = esp32c6_subcircuit(
        vcc_3v3_net=vcc_3v3,
        gnd_net=gnd,
        usb_dp_net=usb_dp,
        usb_dm_net=usb_dm,
        uart_tx_net=esp32_tx,
        uart_rx_net=esp32_rx, 
        enable_net=esp32_en,
        gpio0_net=esp32_io0,
        led_control_net=led_control
    )
    
    # Status LED with current limiting resistor
    led_circuit = led_blinker_subcircuit(
        vcc_3v3_net=vcc_3v3,
        gnd_net=gnd,
        control_net=led_control
    )
    
    return {
        'usb_circuit': usb_circuit,
        'power_circuit': power_circuit,
        'esp32_circuit': esp32_circuit, 
        'led_circuit': led_circuit
    }


if __name__ == "__main__":
    print("🚀 Generating ESP32-C6 Development Board...")
    print("📋 Features: WiFi 6, Bluetooth 5, USB-C, 3.3V regulation")
    
    # Generate the circuit
    circuit_obj = esp32_c6_dev_board()
    
    # Export to KiCad project
    print("📦 Generating KiCad project files...")
    circuit_obj.generate_kicad_project(
        project_name="ESP32_C6_Dev_Board",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    
    print("✅ ESP32-C6 Development Board generated successfully!")
    print("📁 Check the 'kicad-project/' directory for KiCad files")
    print("🎯 Ready for PCB layout and manufacturing!")