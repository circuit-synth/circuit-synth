"""
STM32 Microcontroller Integration.

Provides STM32-specific functionality including:
- Pin mapping and assignment
- Peripheral configuration
- Clock configuration helpers
- Package-specific constraints

This module enables intelligent STM32 circuit design with automatic
pin assignment and configuration validation.
"""

# For backward compatibility, re-export key classes
try:
    from .pin_mapper import STM32PinMapper

    __all__ = ["STM32PinMapper"]

    # Try to import peripheral manager if it exists
    try:
        from .peripheral_manager import STM32PeripheralManager

        __all__.append("STM32PeripheralManager")
    except ImportError:
        pass

except ImportError:
    # Graceful fallback if modules don't exist yet
    __all__ = []
