"""
Project configuration data models for cs-new-project

Defines the configuration options for creating new circuit-synth projects,
including base circuits, example circuits, and project settings.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class BaseCircuit(Enum):
    """Base circuit templates for new projects"""

    RESISTOR_DIVIDER = ("resistor_divider", "Resistor Divider", "Beginner ⭐",
                        "5V → 3.3V logic level shifter (recommended)")
    LED_BLINKER = ("led_blinker", "LED Blinker", "Beginner ⭐",
                   "LED with current limiting resistor")
    VOLTAGE_REGULATOR = ("voltage_regulator", "Voltage Regulator", "Intermediate ⭐⭐",
                         "AMS1117-3.3 linear regulator with decoupling")
    MINIMAL = ("minimal", "Minimal/Empty", "Advanced ⭐⭐⭐",
               "Blank template for experienced users")

    def __init__(self, value: str, display_name: str, difficulty: str, description: str):
        self._value_ = value
        self.display_name = display_name
        self.difficulty = difficulty
        self.description = description


class ExampleCircuit(Enum):
    """Optional example circuit templates"""

    ESP32_DEV_BOARD = ("esp32_dev_board", "ESP32-C6 Dev Board", "Advanced ⭐⭐⭐",
                       "Complete hierarchical dev board with USB-C, power, debug")
    STM32_MINIMAL = ("stm32_minimal", "STM32 Minimal Board", "Advanced ⭐⭐⭐",
                     "STM32F411 with USB, crystal, and SWD debug")
    USB_C_BASIC = ("usb_c_basic", "USB-C Basic Circuit", "Intermediate ⭐⭐",
                   "USB-C connector with CC resistors")
    POWER_SUPPLY = ("power_supply_module", "Power Supply Module", "Intermediate ⭐⭐",
                    "Dual-rail 5V/3.3V power supply")

    def __init__(self, value: str, display_name: str, difficulty: str, description: str):
        self._value_ = value
        self.display_name = display_name
        self.difficulty = difficulty
        self.description = description


@dataclass
class ProjectConfig:
    """Configuration for a new circuit-synth project"""

    base_circuit: BaseCircuit
    examples: List[ExampleCircuit]
    include_agents: bool = True
    include_kicad_plugins: bool = False
    developer_mode: bool = False
    project_name: Optional[str] = None

    def has_examples(self) -> bool:
        """Check if any example circuits are selected"""
        return len(self.examples) > 0

    def get_all_circuits(self) -> List[str]:
        """Get list of all circuit names (base + examples)"""
        circuits = [self.base_circuit.value]
        circuits.extend([ex.value for ex in self.examples])
        return circuits


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
        base_circuit=BaseCircuit.RESISTOR_DIVIDER,
        examples=[],
        include_agents=True,
        include_kicad_plugins=False,
        developer_mode=False
    )
