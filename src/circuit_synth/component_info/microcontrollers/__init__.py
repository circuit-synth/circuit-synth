"""
Microcontroller family integrations.

Provides chip-specific functionality for different MCU families:
- stm32/: STM32 microcontroller family
- esp32/: ESP32 microcontroller family (future)
- pic/: Microchip PIC family (future)
- avr/: Atmel/Microchip AVR family (future)

Key Features:
- Intelligent MCU search with modm-devices integration
- Pin mapping and peripheral assignment
- Manufacturing constraint awareness
"""

# Re-export key classes for easy access
try:
    from .modm_device_search import (
        MCUSearchResult,
        MCUSpecification,
        ModmDeviceSearch,
        print_mcu_result,
        search_by_peripherals,
        search_stm32,
    )
    from .stm32 import STM32PinMapper

    __all__ = [
        "STM32PinMapper",
        "ModmDeviceSearch",
        "MCUSpecification",
        "MCUSearchResult",
        "search_stm32",
        "search_by_peripherals",
        "print_mcu_result",
    ]
except ImportError:
    # Graceful fallback if modules don't exist yet
    __all__ = []
