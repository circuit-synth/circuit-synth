"""
Hierarchical Circuit Design Example

This package demonstrates best practices for organizing circuit-synth projects:

1. **components.py** - Reusable component definitions
2. **power_supply.py** - Single-purpose power supply circuit  
3. **led_indicator.py** - Reusable LED indicator circuits
4. **main_board.py** - Complete system composition

Key principles demonstrated:
- One circuit per file for maintainability
- Clear module boundaries and interfaces
- Component reuse across designs
- Hierarchical composition of complex systems
- Proper documentation and testing
"""

from .components import R_1K, R_10K, R_330, C_100nF, C_10uF, LED_RED, LED_GREEN
from .power_supply import ldo_3v3_regulator
from .led_indicator import status_led, dual_status_leds  
from .main_board import esp32_development_board

__all__ = [
    # Component definitions
    'R_1K', 'R_10K', 'R_330', 'C_100nF', 'C_10uF', 'LED_RED', 'LED_GREEN',
    
    # Circuit functions
    'ldo_3v3_regulator',
    'status_led', 'dual_status_leds',
    'esp32_development_board'
]