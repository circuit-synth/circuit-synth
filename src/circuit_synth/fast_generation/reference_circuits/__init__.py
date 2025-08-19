"""
Reference Circuit Library for Fast Generation

This module contains complete, working circuit-synth examples with proper syntax
for common circuit patterns. These serve as direct references for LLM agents
to generate accurate circuit code.

Available Reference Circuits:
- esp32_basic: ESP32-S3 development board with USB-C and crystal
- esp32_sensor: ESP32-S3 with MPU-6050 IMU and I2C pull-ups  
- stm32_basic: STM32F411 development board with crystal and SWD debug
- motor_stepper: DRV8825 stepper motor driver with current limiting
- led_neopixel: 74AHCT125 level shifter for NeoPixel LED control
- usb_power: USB-C power input with CC resistors and protection

Each file demonstrates:
- Correct circuit-synth syntax with @circuit decorator
- Proper component definitions with verified KiCad symbols
- Pin connections using component["pin"] += net format
- Professional circuit design practices
- KiCad project generation with placement algorithms
"""

from .esp32_basic import esp32_basic
from .esp32_sensor import esp32_sensor
from .stm32_basic import stm32_basic
from .motor_stepper import motor_stepper  
from .led_neopixel import led_neopixel
from .usb_power import usb_power

# Reference circuit catalog for programmatic access
REFERENCE_CIRCUITS = {
    "esp32_basic": {
        "function": esp32_basic,
        "description": "ESP32-S3 development board with USB-C and crystal",
        "components": ["ESP32-S3", "USB-C", "Crystal", "Capacitors", "Debug header"],
        "complexity": 2
    },
    "esp32_sensor": {
        "function": esp32_sensor,
        "description": "ESP32-S3 with MPU-6050 IMU and I2C pull-ups",
        "components": ["ESP32-S3", "MPU-6050", "I2C pull-ups", "USB-C"],
        "complexity": 3
    },
    "stm32_basic": {
        "function": stm32_basic, 
        "description": "STM32F411 development board with crystal and SWD debug",
        "components": ["STM32F411", "Crystal", "SWD header", "Reset circuit"],
        "complexity": 3
    },
    "motor_stepper": {
        "function": motor_stepper,
        "description": "DRV8825 stepper motor driver with current limiting", 
        "components": ["DRV8825", "Current sense", "Motor connector", "Protection"],
        "complexity": 4
    },
    "led_neopixel": {
        "function": led_neopixel,
        "description": "74AHCT125 level shifter for NeoPixel LED control",
        "components": ["74AHCT125", "Level shifter", "NeoPixel connector"],
        "complexity": 3
    },
    "usb_power": {
        "function": usb_power,
        "description": "USB-C power input with CC resistors and protection",
        "components": ["USB-C connector", "CC resistors", "Protection fuse"],
        "complexity": 2
    }
}

def get_reference_circuit(name: str):
    """Get a reference circuit function by name"""
    if name in REFERENCE_CIRCUITS:
        return REFERENCE_CIRCUITS[name]["function"]
    else:
        available = ", ".join(REFERENCE_CIRCUITS.keys())
        raise ValueError(f"Circuit '{name}' not found. Available circuits: {available}")

def list_reference_circuits():
    """List all available reference circuits with descriptions"""
    for name, info in REFERENCE_CIRCUITS.items():
        print(f"• {name}: {info['description']}")
        print(f"  Components: {', '.join(info['components'])}")
        print(f"  Complexity: {info['complexity']}/5")
        print()

__all__ = [
    "esp32_basic", "esp32_sensor", "stm32_basic", 
    "motor_stepper", "led_neopixel", "usb_power",
    "REFERENCE_CIRCUITS", "get_reference_circuit", "list_reference_circuits"
]