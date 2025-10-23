"""
Project configuration data models for cs-new-project

Defines the configuration options for creating new circuit-synth projects.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class Circuit(Enum):
    """Available circuit templates"""

    # Beginner circuits
    RESISTOR_DIVIDER = ("resistor_divider", "Resistor Divider", "Beginner ⭐",
                        "5V → 3.3V logic level shifter", "base_circuits")
    LED_BLINKER = ("led_blinker", "LED Blinker", "Beginner ⭐",
                   "LED with current limiting resistor", "base_circuits")

    # Intermediate circuits
    VOLTAGE_REGULATOR = ("voltage_regulator", "Voltage Regulator", "Intermediate ⭐⭐",
                         "AMS1117-3.3 linear regulator with decoupling", "base_circuits")
    USB_C_BASIC = ("usb_c_basic", "USB-C Basic Circuit", "Intermediate ⭐⭐",
                   "USB-C connector with CC resistors", "example_circuits")
    POWER_SUPPLY = ("power_supply_module", "Power Supply Module", "Intermediate ⭐⭐",
                    "Dual-rail 5V/3.3V power supply", "example_circuits")

    # Advanced circuits
    ESP32_DEV_BOARD = ("esp32_dev_board", "ESP32-C6 Dev Board", "Advanced ⭐⭐⭐",
                       "Minimal ESP32 integration example", "example_circuits")
    STM32_MINIMAL = ("stm32_minimal", "STM32 Minimal Board", "Advanced ⭐⭐⭐",
                     "STM32F411 with USB, crystal, and SWD debug", "example_circuits")

    # Empty template
    MINIMAL = ("minimal", "Minimal/Empty", "Expert",
               "Blank template for experienced users", "base_circuits")

    def __init__(self, value: str, display_name: str, difficulty: str, description: str, template_dir: str):
        self._value_ = value
        self.display_name = display_name
        self.difficulty = difficulty
        self.description = description
        self.template_dir = template_dir  # base_circuits or example_circuits


@dataclass
class ProjectConfig:
    """Configuration for a new circuit-synth project"""

    circuits: List[Circuit]
    include_agents: bool = True
    include_kicad_plugins: bool = False
    developer_mode: bool = False
    project_name: Optional[str] = None

    def has_circuits(self) -> bool:
        """Check if any circuits are selected"""
        return len(self.circuits) > 0

    def get_circuit_names(self) -> List[str]:
        """Get list of all circuit names"""
        return [circuit.value for circuit in self.circuits]


@dataclass
class CircuitTemplate:
    """Metadata for a circuit template"""

    name: str
    display_name: str
    difficulty: str
    description: str
    code: str
    estimated_bom_cost: str = "$0.02-0.50"
    complexity_level: str = "beginner"  # beginner, intermediate, advanced


def get_default_config() -> ProjectConfig:
    """Get default project configuration for quick start"""
    return ProjectConfig(
        circuits=[Circuit.RESISTOR_DIVIDER],
        include_agents=True,
        include_kicad_plugins=False,
        developer_mode=False
    )
