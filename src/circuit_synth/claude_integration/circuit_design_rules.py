"""
Circuit Design Rules Knowledge Base

This module provides essential circuit design rules and best practices
that all circuit design agents must use for research and validation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class ComponentType(Enum):
    """Component classification for design rules"""

    MICROCONTROLLER = "microcontroller"
    POWER_MANAGEMENT = "power_management"
    ANALOG = "analog"
    DIGITAL = "digital"
    PASSIVE = "passive"
    CONNECTOR = "connector"
    SENSOR = "sensor"
    COMMUNICATION = "communication"


@dataclass
class DesignRule:
    """Represents a circuit design rule"""

    rule_id: str
    description: str
    applies_to: List[ComponentType]
    rationale: str
    examples: List[str]
    violations_cause: str
    priority: str  # "critical", "important", "recommended"


@dataclass
class ComponentRequirement:
    """Specific component requirements for different applications"""

    component_family: str
    typical_values: Dict[str, str]
    design_considerations: List[str]
    common_mistakes: List[str]


class CircuitDesignRules:
    """
    Comprehensive circuit design rules knowledge base.

    This class provides essential design rules that must be followed
    by all circuit design agents to ensure robust, manufacturable designs.
    """

    @staticmethod
    def get_critical_rules() -> List[DesignRule]:
        """Get critical design rules that must never be violated"""
        return [
            DesignRule(
                rule_id="POWER_DECOUPLING_MANDATORY",
                description="Every IC must have at least one decoupling capacitor",
                applies_to=[
                    ComponentType.MICROCONTROLLER,
                    ComponentType.ANALOG,
                    ComponentType.DIGITAL,
                ],
                rationale="Decoupling capacitors filter power supply noise, reduce EMI, and provide instantaneous current during switching",
                examples=[
                    "0.1µF ceramic capacitor close to each VCC pin",
                    "10µF electrolytic for bulk decoupling",
                    "Multiple values (0.1µF + 1µF) for broad frequency coverage",
                ],
                violations_cause="Power supply noise, EMI issues, unstable operation, potential latch-up",
                priority="critical",
            ),
            DesignRule(
                rule_id="USB_SERIES_RESISTORS",
                description="USB data lines must have 22Ω series resistors",
                applies_to=[ComponentType.COMMUNICATION],
                rationale="USB 2.0 specification requires impedance matching and signal integrity for differential pair",
                examples=[
                    "22Ω ±1% resistors on D+ and D- lines",
                    "Place resistors as close as possible to the driving IC",
                    "Use precision resistors (1% tolerance or better)",
                ],
                violations_cause="USB enumeration failures, signal integrity issues, EMC compliance problems",
                priority="critical",
            ),
            DesignRule(
                rule_id="CRYSTAL_LOADING_CAPACITORS",
                description="Crystals require proper loading capacitors for stable oscillation",
                applies_to=[ComponentType.MICROCONTROLLER],
                rationale="Loading capacitors set the crystal's operating frequency and ensure stable oscillation",
                examples=[
                    "Typical values: 18-22pF for most microcontroller crystals",
                    "Match crystal manufacturer's specifications",
                    "Place capacitors as close as possible to crystal and MCU pins",
                ],
                violations_cause="Clock instability, frequency drift, startup failures",
                priority="critical",
            ),
            DesignRule(
                rule_id="RESET_PULLUP_REQUIRED",
                description="Reset pins must have pull-up resistors",
                applies_to=[ComponentType.MICROCONTROLLER],
                rationale="Ensures defined logic level when reset is not actively driven, prevents spurious resets",
                examples=[
                    "10kΩ pull-up resistor to VCC",
                    "Add 0.1µF capacitor to GND for reset debouncing",
                    "Use Schmitt trigger buffers for noisy environments",
                ],
                violations_cause="Random resets, unstable startup, undefined behavior",
                priority="critical",
            ),
        ]

    @staticmethod
    def get_important_rules() -> List[DesignRule]:
        """Get important design rules that should be followed"""
        return [
            DesignRule(
                rule_id="BYPASS_CAPACITOR_PLACEMENT",
                description="Place bypass capacitors as close as possible to IC power pins",
                applies_to=[ComponentType.MICROCONTROLLER, ComponentType.ANALOG],
                rationale="Minimize inductance in the power delivery path for effective high-frequency decoupling",
                examples=[
                    "Place within 5mm of IC power pins",
                    "Use wide, short traces to reduce inductance",
                    "Via directly to power/ground planes when possible",
                ],
                violations_cause="Reduced decoupling effectiveness, potential oscillations",
                priority="important",
            ),
            DesignRule(
                rule_id="ANALOG_DIGITAL_SEPARATION",
                description="Separate analog and digital power/ground domains",
                applies_to=[ComponentType.ANALOG, ComponentType.MICROCONTROLLER],
                rationale="Prevents digital switching noise from corrupting sensitive analog signals",
                examples=[
                    "Separate AVCC/DVCC pins with ferrite bead or inductor",
                    "Split ground planes with single connection point",
                    "Dedicated analog reference voltage regulation",
                ],
                violations_cause="Increased ADC noise, poor analog performance",
                priority="important",
            ),
            DesignRule(
                rule_id="I2C_PULLUP_RESISTORS",
                description="I²C buses require pull-up resistors on SDA and SCL",
                applies_to=[ComponentType.COMMUNICATION],
                rationale="I²C is open-drain, requires pull-ups for proper high-level voltage",
                examples=[
                    "Typical values: 4.7kΩ for standard speed (100kHz)",
                    "2.2kΩ for fast mode (400kHz)",
                    "1kΩ for fast mode plus (1MHz)",
                ],
                violations_cause="I²C communication failures, signal integrity issues",
                priority="important",
            ),
            DesignRule(
                rule_id="SPI_SIGNAL_INTEGRITY",
                description="SPI signals require proper termination for high-speed operation",
                applies_to=[ComponentType.COMMUNICATION],
                rationale="High-speed SPI signals need controlled impedance and proper termination",
                examples=[
                    "33Ω series resistors for signal integrity",
                    "Keep traces short and impedance controlled",
                    "Match trace lengths for synchronized signals",
                ],
                violations_cause="Data corruption, timing violations, EMI",
                priority="important",
            ),
            DesignRule(
                rule_id="POWER_SUPPLY_FILTERING",
                description="Power supplies need proper input and output filtering",
                applies_to=[ComponentType.POWER_MANAGEMENT],
                rationale="Reduces ripple, improves regulation, prevents oscillation",
                examples=[
                    "Input: 10µF+ bulk capacitor + 0.1µF ceramic",
                    "Output: ESR-appropriate capacitor for stability",
                    "Follow regulator datasheet recommendations",
                ],
                violations_cause="Poor regulation, oscillation, increased ripple",
                priority="important",
            ),
        ]

    @staticmethod
    def get_component_requirements() -> Dict[str, ComponentRequirement]:
        """Get specific component requirements by family"""
        return {
            "stm32_microcontroller": ComponentRequirement(
                component_family="STM32 Microcontroller",
                typical_values={
                    "decoupling_cap": "0.1µF ceramic (X7R/X5R)",
                    "bulk_cap": "10µF ceramic or tantalum",
                    "crystal_caps": "18-22pF (check datasheet)",
                    "reset_pullup": "10kΩ",
                    "boot_pullup": "10kΩ (BOOT0 pin)",
                    "vref_cap": "1µF + 10nF (if using ADC)",
                },
                design_considerations=[
                    "Separate AVDD/AVSS for analog-heavy applications",
                    "BOOT0 pin determines boot source (pulldown for flash)",
                    "HSE crystal placement critical for USB applications",
                    "NRST requires RC circuit for proper reset timing",
                    "Consider LSE crystal for RTC applications",
                ],
                common_mistakes=[
                    "Forgetting BOOT0 pulldown resistor",
                    "Inadequate decoupling on analog supplies",
                    "Crystal placement too far from MCU pins",
                    "Missing VREF+ decoupling for ADC use",
                ],
            ),
            "esp32_module": ComponentRequirement(
                component_family="ESP32 Module",
                typical_values={
                    "decoupling_cap": "0.1µF + 10µF ceramic",
                    "enable_pullup": "10kΩ (EN pin)",
                    "gpio0_pullup": "10kΩ (for normal boot)",
                    "antenna_matching": "Per module datasheet",
                },
                design_considerations=[
                    "EN pin needs pull-up for normal operation",
                    "GPIO0 pulled high for normal boot, low for download",
                    "Keep antenna traces away from high-speed signals",
                    "3.3V supply must handle WiFi current spikes (up to 500mA)",
                    "Consider module vs bare chip for RF complexity",
                ],
                common_mistakes=[
                    "Insufficient power supply current capacity",
                    "Poor antenna routing causing RF issues",
                    "Missing pull-ups on critical pins",
                    "Inadequate power supply decoupling",
                ],
            ),
            "imu_sensor": ComponentRequirement(
                component_family="IMU Sensor",
                typical_values={
                    "decoupling_cap": "0.1µF ceramic close to VDD",
                    "i2c_pullups": "4.7kΩ (for I²C interface)",
                    "spi_termination": "33Ω series (for SPI interface)",
                },
                design_considerations=[
                    "Choose I²C or SPI interface based on speed requirements",
                    "Consider interrupt pins for efficient data reading",
                    "Mechanical isolation from vibration sources",
                    "Temperature compensation for precision applications",
                    "Orientation marking for consistent mounting",
                ],
                common_mistakes=[
                    "Mounting sensor rigidly to high-vibration areas",
                    "Forgetting interrupt pin connections",
                    "Poor power supply filtering causing noise",
                    "Incorrect I²C address configuration",
                ],
            ),
            "usb_connector": ComponentRequirement(
                component_family="USB Connector",
                typical_values={
                    "data_series_r": "22Ω ±1% (D+, D-)",
                    "shield_connection": "Ferrite bead + 1MΩ to GND",
                    "esd_protection": "Low capacitance TVS diodes",
                    "vbus_filter": "Ferrite bead + capacitor",
                },
                design_considerations=[
                    "USB-C requires proper CC pin handling",
                    "Shield connection for EMI suppression",
                    "ESD protection on all exposed pins",
                    "Differential pair routing with 90Ω impedance",
                    "Keep data traces matched length",
                ],
                common_mistakes=[
                    "Missing or incorrect series resistors",
                    "Poor differential pair routing",
                    "Inadequate ESD protection",
                    "Shield connected directly to ground",
                ],
            ),
        }

    @staticmethod
    def get_protocol_requirements(protocol: str) -> Optional[Dict[str, str]]:
        """Get specific requirements for communication protocols"""
        protocols = {
            "uart": {
                "voltage_levels": "3.3V CMOS or RS232 levels",
                "termination": "Not required for short distances",
                "considerations": "Use level shifters for voltage mismatch",
                "common_baud_rates": "9600, 115200, 921600 bps",
            },
            "spi": {
                "voltage_levels": "Match master and slave levels",
                "termination": "33Ω series resistors for high speed",
                "considerations": "CPOL/CPHA must match, keep traces short",
                "max_frequency": "Depends on load and trace length",
            },
            "i2c": {
                "voltage_levels": "1.8V, 3.3V, or 5V (open-drain)",
                "pullup_resistors": "4.7kΩ (100kHz), 2.2kΩ (400kHz), 1kΩ (1MHz)",
                "considerations": "7-bit vs 10-bit addressing, multi-master support",
                "bus_capacitance": "400pF maximum",
            },
            "usb2": {
                "voltage_levels": "3.3V CMOS for logic, 5V for VBUS",
                "impedance": "90Ω differential, 22Ω series resistors",
                "considerations": "Matched length traces, proper termination",
                "max_length": "5m for high-speed, 3m for full-speed",
            },
            "can": {
                "voltage_levels": "5V differential signaling",
                "termination": "120Ω resistors at each end of bus",
                "considerations": "Twisted pair cable, star topology forbidden",
                "max_speed": "1Mbps (depends on network length)",
            },
        }

        return protocols.get(protocol.lower())

    @staticmethod
    def validate_circuit_requirements(
        circuit_type: str, components: List[str]
    ) -> List[str]:
        """
        Validate circuit against design rules and return issues/recommendations
        """
        issues = []

        # Check for microcontroller requirements
        if any(
            "stm32" in comp.lower() or "esp32" in comp.lower() for comp in components
        ):
            if not any("capacitor" in comp.lower() for comp in components):
                issues.append(
                    "CRITICAL: Microcontroller present but no decoupling capacitors found"
                )

            if "stm32" in " ".join(components).lower():
                if not any("crystal" in comp.lower() for comp in components):
                    issues.append(
                        "IMPORTANT: STM32 without crystal - consider HSE requirements"
                    )
                if not any(
                    "reset" in comp.lower() or "pullup" in comp.lower()
                    for comp in components
                ):
                    issues.append("IMPORTANT: STM32 reset pin needs pull-up resistor")

        # Check for USB requirements
        if any("usb" in comp.lower() for comp in components):
            if not any(
                "22" in comp and "resistor" in comp.lower() for comp in components
            ):
                issues.append("CRITICAL: USB interface missing 22Ω series resistors")
            if not any(
                "esd" in comp.lower() or "tvs" in comp.lower() for comp in components
            ):
                issues.append("IMPORTANT: USB interface should include ESD protection")

        # Check for I2C requirements
        if "i2c" in circuit_type.lower() or any(
            "i2c" in comp.lower() for comp in components
        ):
            if not any(
                "pullup" in comp.lower() and "resistor" in comp.lower()
                for comp in components
            ):
                issues.append("CRITICAL: I2C bus missing pull-up resistors")

        return issues

    @staticmethod
    def get_research_prompts() -> Dict[str, str]:
        """Get research prompts for different circuit types to guide agent research"""
        return {
            "stm32_circuit": """
            Research STM32 microcontroller circuit design:
            1. Identify STM32 family requirements (power supply, decoupling)
            2. Check crystal/oscillator requirements for target application
            3. Determine reset circuit topology and pull-up values
            4. Verify BOOT0 pin configuration for target boot source
            5. Consider analog supply separation if using ADC/DAC
            6. Review HSE requirements for USB or precision timing
            """,
            "esp32_circuit": """
            Research ESP32 module circuit design:
            1. Identify module vs bare chip requirements
            2. Check power supply requirements (3.3V, current spikes)
            3. Determine EN pin pull-up configuration
            4. Verify GPIO0/GPIO2 boot pin configurations
            5. Consider antenna requirements and RF layout
            6. Review strapping pin requirements
            """,
            "usb_circuit": """
            Research USB interface circuit design:
            1. Identify USB version requirements (2.0, 3.0, USB-C)
            2. Check differential pair impedance requirements (90Ω)
            3. Determine series resistor values (typically 22Ω)
            4. Consider ESD protection requirements
            5. Review VBUS power management and protection
            6. Check connector mechanical requirements
            """,
            "power_supply": """
            Research power supply circuit design:
            1. Determine input voltage range and protection
            2. Calculate output current and efficiency requirements
            3. Check regulator stability and compensation
            4. Design input and output filtering
            5. Consider thermal management and heatsinking
            6. Review protection features (OCP, OVP, thermal)
            """,
            "sensor_interface": """
            Research sensor interface circuit design:
            1. Identify sensor communication protocol (I2C, SPI, analog)
            2. Check power supply requirements and filtering
            3. Determine signal conditioning requirements
            4. Consider environmental protection (ESD, overvoltage)
            5. Review calibration and compensation methods
            6. Check interrupt/data ready signal handling
            """,
        }


def get_design_rules_context(circuit_type: str) -> str:
    """
    Get relevant design rules context for a specific circuit type.
    This is used by agents to understand what rules to follow.
    """
    rules = CircuitDesignRules()
    critical_rules = rules.get_critical_rules()
    important_rules = rules.get_important_rules()

    # Filter rules relevant to circuit type
    relevant_rules = []
    circuit_lower = circuit_type.lower()

    if any(
        keyword in circuit_lower
        for keyword in ["mcu", "microcontroller", "stm32", "esp32"]
    ):
        relevant_rules.extend(
            [r for r in critical_rules if ComponentType.MICROCONTROLLER in r.applies_to]
        )

    if any(keyword in circuit_lower for keyword in ["usb", "communication"]):
        relevant_rules.extend(
            [r for r in critical_rules if ComponentType.COMMUNICATION in r.applies_to]
        )

    if any(keyword in circuit_lower for keyword in ["power", "supply", "regulator"]):
        relevant_rules.extend(
            [
                r
                for r in important_rules
                if ComponentType.POWER_MANAGEMENT in r.applies_to
            ]
        )

    # Build context string
    context = f"## Circuit Design Rules for {circuit_type}\n\n"

    for rule in relevant_rules:
        context += f"### {rule.rule_id} ({rule.priority.upper()})\n"
        context += f"**Rule**: {rule.description}\n"
        context += f"**Why**: {rule.rationale}\n"
        context += f"**Examples**: {', '.join(rule.examples)}\n"
        context += f"**Violations cause**: {rule.violations_cause}\n\n"

    # Add research prompt if available
    research_prompts = rules.get_research_prompts()
    for prompt_type, prompt_text in research_prompts.items():
        if any(keyword in circuit_lower for keyword in prompt_type.split("_")):
            context += f"## Research Requirements\n{prompt_text}\n"
            break

    return context
