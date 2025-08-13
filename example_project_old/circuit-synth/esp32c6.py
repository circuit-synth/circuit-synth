#!/usr/bin/env python3
"""
ESP32-C6 Microcontroller Subcircuit
===================================

ESP32-C6-MINI-1 module with crystal oscillator, reset circuitry,
and GPIO breakout. Provides WiFi 6, Bluetooth 5, Thread, and Zigbee.
"""

from circuit_synth import Component, Net, circuit


@circuit(name="ESP32_C6_Microcontroller")
def esp32c6_subcircuit(vcc_3v3_net, gnd_net, usb_dp_net, usb_dm_net, 
                      uart_tx_net, uart_rx_net, enable_net, gpio0_net, led_control_net):
    """
    ESP32-C6-MINI-1 microcontroller subcircuit
    
    Features:
    - ESP32-C6-MINI-1 module (WiFi 6, BLE 5, Thread, Zigbee)
    - Crystal oscillator for accurate timing
    - Reset button and boot mode control
    - USB programming interface
    - GPIO pin breakout
    - Proper power decoupling
    
    Args:
        vcc_3v3_net: 3.3V power supply net
        gnd_net: System ground net
        usb_dp_net: USB D+ data net
        usb_dm_net: USB D- data net  
        uart_tx_net: UART transmit for programming
        uart_rx_net: UART receive for programming
        enable_net: ESP32 enable/reset net
        gpio0_net: Boot mode control (GPIO0)
        led_control_net: Status LED control GPIO
    """
    
    # ESP32-C6-MINI-1 module
    # Complete module with integrated flash, antenna, and RF circuitry
    esp32_module = Component(
        symbol="RF_Module:ESP32-C6-MINI-1",
        ref="U",
        footprint="RF_Module:ESP32-C6-MINI-1"
    )
    
    # Crystal oscillator (40MHz for ESP32-C6)
    # Provides accurate clock reference for WiFi/BLE timing
    crystal = Component(
        symbol="Device:Crystal",
        ref="Y",
        value="40MHz",
        footprint="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm"
    )
    
    # Crystal loading capacitors
    # Typically 10-22pF depending on crystal specifications
    xtal_cap1 = Component(
        symbol="Device:C",
        ref="C", 
        value="18pF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    xtal_cap2 = Component(
        symbol="Device:C",
        ref="C",
        value="18pF", 
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Reset button
    # Manual reset capability for development
    reset_button = Component(
        symbol="Switch:SW_Push",
        ref="SW",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3"
    )
    
    # Reset pull-up resistor  
    # Keeps ESP32 enabled when button not pressed
    reset_pullup = Component(
        symbol="Device:R",
        ref="R",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric" 
    )
    
    # Boot mode button (GPIO0)
    # Allows entering bootloader for programming
    boot_button = Component(
        symbol="Switch:SW_Push", 
        ref="SW",
        footprint="Button_Switch_SMD:SW_SPST_CK_RS282G05A3"
    )
    
    # GPIO0 pull-up resistor
    # Ensures normal boot when button not pressed
    gpio0_pullup = Component(
        symbol="Device:R",
        ref="R", 
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Power decoupling capacitors
    # Provide clean power to ESP32 module
    power_cap1 = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    power_cap2 = Component(
        symbol="Device:C", 
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # ESP32-C6 power connections
    esp32_module["VDD"] += vcc_3v3_net
    esp32_module["VSS"] += gnd_net
    esp32_module["GND"] += gnd_net
    
    # USB interface (built-in USB serial converter)
    esp32_module["USB_D+"] += usb_dp_net  
    esp32_module["USB_D-"] += usb_dm_net
    
    # UART programming interface
    esp32_module["TXD0"] += uart_tx_net
    esp32_module["RXD0"] += uart_rx_net
    
    # Reset and boot control
    esp32_module["EN"] += enable_net
    esp32_module["IO0"] += gpio0_net
    
    # LED control GPIO
    esp32_module["IO8"] += led_control_net  # Use GPIO8 for LED control
    
    # Crystal connections
    esp32_module["XTAL_32K_P"] += crystal[1]
    esp32_module["XTAL_32K_N"] += crystal[2]
    
    # Crystal loading capacitors
    crystal[1] += xtal_cap1[1]
    xtal_cap1[2] += gnd_net
    crystal[2] += xtal_cap2[1] 
    xtal_cap2[2] += gnd_net
    
    # Reset button circuit
    vcc_3v3_net += reset_pullup[1]
    reset_pullup[2] += enable_net
    reset_button[1] += enable_net
    reset_button[2] += gnd_net
    
    # Boot button circuit (GPIO0)
    vcc_3v3_net += gpio0_pullup[1]
    gpio0_pullup[2] += gpio0_net
    boot_button[1] += gpio0_net
    boot_button[2] += gnd_net
    
    # Power decoupling
    power_cap1[1] += vcc_3v3_net
    power_cap1[2] += gnd_net
    power_cap2[1] += vcc_3v3_net  
    power_cap2[2] += gnd_net
    
    return locals()


if __name__ == "__main__":
    print("🔌 Testing ESP32-C6 subcircuit...")
    
    # Create test nets
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    usb_dp = Net('USB_DP')
    usb_dm = Net('USB_DM')
    uart_tx = Net('UART_TX')
    uart_rx = Net('UART_RX')  
    enable = Net('ESP32_EN')
    gpio0 = Net('ESP32_IO0')
    led_ctrl = Net('LED_CONTROL')
    
    # Test the subcircuit
    circuit_obj = esp32c6_subcircuit(
        vcc_3v3, gnd, usb_dp, usb_dm, uart_tx, uart_rx, 
        enable, gpio0, led_ctrl
    )
    
    print("✅ ESP32-C6 subcircuit created successfully")
    print(f"📊 Components: {len(circuit_obj.to_dict()['components'])}")  
    print("📋 Features: ESP32-C6 module, crystal, reset/boot buttons, decoupling")