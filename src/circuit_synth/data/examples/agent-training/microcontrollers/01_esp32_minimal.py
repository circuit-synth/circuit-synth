#!/usr/bin/env python3
"""
CIRCUIT: ESP32-S3 Minimal Configuration
PURPOSE: Basic ESP32-S3 setup with power, programming, and essential peripherals
COMPONENTS: ESP32-S3-MINI-1 module + decoupling + reset + boot + LED indicator
COMPLEXITY: Beginner
DOMAIN: Microcontroller Design
"""

from circuit_synth import Circuit, Component, Net, circuit


@circuit
def esp32_minimal():
    """
    Minimal ESP32-S3 configuration with essential connections.

    Design Notes:
    - ESP32-S3-MINI-1 integrates flash, crystal, and power management
    - 3.3V power supply required (2.3V-3.6V operating range)
    - 10µF decoupling capacitor for stable power delivery
    - Pull-up resistor on EN pin for proper reset operation
    - Pull-up resistor on IO0 for normal boot mode
    - LED indicator on GPIO2 with current limiting resistor
    - Exposed EN and IO0 pins for programming interface

    ESP32-S3 Key Pins:
    - Pin 1: GND (ground reference)
    - Pin 2: 3V3 (power input, 3.3V)
    - Pin 3: EN (enable/reset, active high)
    - Pin 4: IO4 (GPIO4, general purpose)
    - Pin 41: IO0 (boot mode selection)
    - Pin 42: IO2 (LED output, safe for GPIO)
    """
    # Create power and signal nets
    vcc_3v3 = Net("VCC_3V3")  # 3.3V power supply
    gnd = Net("GND")  # Ground reference

    # Reset and boot control nets
    esp32_en = Net("ESP32_EN")  # Enable/reset signal
    esp32_io0 = Net("ESP32_IO0")  # Boot mode control
    esp32_io2 = Net("ESP32_IO2")  # GPIO2 for LED

    # ESP32-S3-MINI-1 module
    # Integrated module with ESP32-S3, 8MB flash, crystal, and power management
    esp32 = Component(
        symbol="RF_Module:ESP32-S3-MINI-1",
        ref="U1",
        footprint="RF_Module:ESP32-S3-MINI-1",
    )

    # Power supply decoupling capacitor
    # 10µF ceramic capacitor for stable power delivery
    cap_power = Component(
        symbol="Device:C",
        ref="C1",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )

    # EN pin pull-up resistor
    # 10K pull-up ensures proper reset operation
    r_en_pullup = Component(
        symbol="Device:R",
        ref="R1",
        value="10K",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # IO0 pin pull-up resistor
    # 10K pull-up for normal boot mode (high = normal, low = download)
    r_io0_pullup = Component(
        symbol="Device:R",
        ref="R2",
        value="10K",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # LED current limiting resistor
    # 330Ω limits current to ~8mA at 3.3V
    r_led = Component(
        symbol="Device:R",
        ref="R3",
        value="330R",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Status LED indicator
    # Connected to GPIO2 (safe pin, no boot conflicts)
    led_status = Component(
        symbol="Device:LED",
        ref="D1",
        value="LED",
        footprint="LED_SMD:LED_0603_1608Metric",
    )

    # ESP32 power connections (using integer pin access)
    esp32[1] += gnd  # Pin 1: GND
    esp32[2] += vcc_3v3  # Pin 2: 3V3 power input

    # ESP32 control pins
    esp32[3] += esp32_en  # Pin 3: EN (enable/reset)
    esp32[41] += esp32_io0  # Pin 41: IO0 (boot mode)
    esp32[42] += esp32_io2  # Pin 42: IO2 (GPIO for LED)

    # Power supply decoupling
    cap_power[1] += vcc_3v3  # Positive terminal to 3.3V
    cap_power[2] += gnd  # Negative terminal to ground

    # EN pin pull-up (enables normal operation)
    r_en_pullup[1] += esp32_en  # Connect to EN pin
    r_en_pullup[2] += vcc_3v3  # Pull up to 3.3V

    # IO0 pin pull-up (normal boot mode)
    r_io0_pullup[1] += esp32_io0  # Connect to IO0 pin
    r_io0_pullup[2] += vcc_3v3  # Pull up to 3.3V

    # LED circuit (status indicator)
    r_led[1] += esp32_io2  # Current limiting resistor from GPIO2
    r_led[2] += led_status[1]  # Connect to LED anode
    led_status[2] += gnd  # LED cathode to ground
