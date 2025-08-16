"""
Circuit Pattern Templates for Fast Generation

Pre-defined circuit patterns with verified KiCad components.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class PatternType(Enum):
    """Available circuit pattern types"""
    ESP32_BASIC = "esp32_basic"
    ESP32_SENSOR = "esp32_sensor"  
    STM32_BASIC = "stm32_basic"
    STM32_MOTOR = "stm32_motor"
    MOTOR_STEPPER = "motor_stepper"
    SENSOR_IMU = "sensor_imu"
    SENSOR_TEMP = "sensor_temp"
    LED_NEOPIXEL = "led_neopixel" 
    USB_POWER = "usb_power"
    ENCODER_QUAD = "encoder_quad"


@dataclass
class ComponentSpec:
    """Specification for a circuit component"""
    symbol: str           # KiCad symbol (Library:Symbol)
    footprint: str        # KiCad footprint (Library:Footprint)
    value: str           # Component value
    ref_prefix: str      # Reference designator prefix
    description: str     # Human description
    required: bool = True # Whether component is mandatory
    alternatives: List[str] = None  # Alternative symbols


@dataclass 
class PatternTemplate:
    """Template for a circuit pattern"""
    name: str
    description: str
    components: List[ComponentSpec]
    connections: List[Dict[str, str]]  # Connection specifications
    power_rails: List[str]             # Required power rails
    design_notes: List[str]            # Design considerations
    estimated_complexity: int         # 1-5 complexity rating


class CircuitPatterns:
    """Repository of verified circuit patterns"""
    
    @staticmethod
    def get_pattern(pattern_type: PatternType) -> PatternTemplate:
        """Get pattern template by type"""
        patterns = {
            PatternType.ESP32_BASIC: CircuitPatterns._esp32_basic(),
            PatternType.ESP32_SENSOR: CircuitPatterns._esp32_sensor(),
            PatternType.STM32_BASIC: CircuitPatterns._stm32_basic(), 
            PatternType.STM32_MOTOR: CircuitPatterns._stm32_motor(),
            PatternType.MOTOR_STEPPER: CircuitPatterns._motor_stepper(),
            PatternType.SENSOR_IMU: CircuitPatterns._sensor_imu(),
            PatternType.SENSOR_TEMP: CircuitPatterns._sensor_temp(),
            PatternType.LED_NEOPIXEL: CircuitPatterns._led_neopixel(),
            PatternType.USB_POWER: CircuitPatterns._usb_power(),
            PatternType.ENCODER_QUAD: CircuitPatterns._encoder_quad(),
        }
        
        return patterns.get(pattern_type)
    
    @staticmethod
    def list_patterns() -> List[Dict[str, Any]]:
        """List all available patterns with metadata"""
        return [
            {
                "type": pattern_type,
                "name": CircuitPatterns.get_pattern(pattern_type).name,
                "description": CircuitPatterns.get_pattern(pattern_type).description,
                "complexity": CircuitPatterns.get_pattern(pattern_type).estimated_complexity
            }
            for pattern_type in PatternType
        ]
    
    # Pattern Definitions
    
    @staticmethod
    def _esp32_basic() -> PatternTemplate:
        """Basic ESP32 development board pattern"""
        return PatternTemplate(
            name="ESP32 Basic Development Board",
            description="Minimal ESP32-S3 board with USB-C, debug, and basic I/O",
            components=[
                ComponentSpec(
                    symbol="MCU_Espressif:ESP32-S3",
                    footprint="Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP5.6x5.6mm",
                    value="ESP32-S3",
                    ref_prefix="U",
                    description="Main ESP32-S3 microcontroller"
                ),
                ComponentSpec(
                    symbol="Connector:USB_C_Receptacle_USB2.0_16P", 
                    footprint="Connector_USB:USB_C_Receptacle_GCT_USB4085",
                    value="USB-C",
                    ref_prefix="J",
                    description="USB-C connector for power and data"
                ),
                ComponentSpec(
                    symbol="Device:Crystal",
                    footprint="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
                    value="40MHz",
                    ref_prefix="Y",
                    description="Main crystal oscillator"
                ),
                ComponentSpec(
                    symbol="Device:C",
                    footprint="Capacitor_SMD:C_0603_1608Metric",
                    value="22pF",
                    ref_prefix="C",
                    description="Crystal load capacitors"
                ),
                ComponentSpec(
                    symbol="Device:C", 
                    footprint="Capacitor_SMD:C_0603_1608Metric",
                    value="100nF",
                    ref_prefix="C",
                    description="Decoupling capacitors"
                ),
                ComponentSpec(
                    symbol="Device:R",
                    footprint="Resistor_SMD:R_0603_1608Metric", 
                    value="10k",
                    ref_prefix="R",
                    description="Pull-up resistors"
                )
            ],
            connections=[
                {"from": "U1.VDD", "to": "3V3_RAIL"},
                {"from": "U1.VSS", "to": "GND"},
                {"from": "J1.VBUS", "to": "5V_RAIL"},
                {"from": "Y1.1", "to": "U1.GPIO0"}, 
                {"from": "Y1.2", "to": "U1.GPIO1"}
            ],
            power_rails=["3V3", "GND", "5V"],
            design_notes=[
                "Add decoupling capacitors near each power pin",
                "Include pull-up resistors on I2C lines if used",
                "Route high-speed signals with controlled impedance",
                "Add test points for debug signals"
            ],
            estimated_complexity=2
        )
    
    @staticmethod
    def _esp32_sensor() -> PatternTemplate:
        """ESP32 with IMU sensor integration"""
        return PatternTemplate(
            name="ESP32 with IMU Sensor",
            description="ESP32-S3 with MPU-6050 IMU sensor via I2C",
            components=[
                ComponentSpec(
                    symbol="MCU_Espressif:ESP32-S3",
                    footprint="Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP5.6x5.6mm",
                    value="ESP32-S3",
                    ref_prefix="U",
                    description="Main ESP32-S3 microcontroller"
                ),
                ComponentSpec(
                    symbol="Sensor_Motion:MPU-6050", 
                    footprint="Sensor_Motion:InvenSense_QFN-24_4x4mm_P0.5mm",
                    value="MPU-6050",
                    ref_prefix="U",
                    description="6-axis IMU sensor"
                ),
                ComponentSpec(
                    symbol="Device:R",
                    footprint="Resistor_SMD:R_0603_1608Metric",
                    value="4.7k", 
                    ref_prefix="R",
                    description="I2C pull-up resistors"
                )
            ],
            connections=[
                {"from": "U2.VDD", "to": "3V3_RAIL"},
                {"from": "U2.GND", "to": "GND"},
                {"from": "U2.SCL", "to": "U1.GPIO22"},
                {"from": "U2.SDA", "to": "U1.GPIO21"}
            ],
            power_rails=["3V3", "GND"],
            design_notes=[
                "Add I2C pull-up resistors (4.7k typical)",
                "Keep I2C traces short and away from switching signals", 
                "Consider adding filtering capacitor on sensor power",
                "Mount IMU away from magnetic interference"
            ],
            estimated_complexity=2
        )
    
    @staticmethod  
    def _stm32_basic() -> PatternTemplate:
        """Basic STM32F4 development board"""
        return PatternTemplate(
            name="STM32F4 Basic Board",
            description="STM32F4 microcontroller with debug and basic peripherals",
            components=[
                ComponentSpec(
                    symbol="MCU_ST_STM32F4:STM32F407VETx",
                    footprint="Package_QFP:LQFP-100_14x14mm_P0.5mm",
                    value="STM32F407VET6",
                    ref_prefix="U", 
                    description="STM32F4 microcontroller"
                ),
                ComponentSpec(
                    symbol="Device:Crystal",
                    footprint="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", 
                    value="8MHz",
                    ref_prefix="Y",
                    description="HSE crystal"
                ),
                ComponentSpec(
                    symbol="Connector:Conn_ARM_JTAG_SWD_10",
                    footprint="Connector_PinSocket_1.27mm:PinSocket_2x05_P1.27mm_Vertical",
                    value="SWD",
                    ref_prefix="J",
                    description="SWD debug connector"
                )
            ],
            connections=[
                {"from": "U1.VDD", "to": "3V3_RAIL"},
                {"from": "U1.VSS", "to": "GND"},
                {"from": "J1.SWDIO", "to": "U1.PA13"},
                {"from": "J1.SWCLK", "to": "U1.PA14"}
            ],
            power_rails=["3V3", "GND"],
            design_notes=[
                "Add bypass capacitors on all VDD pins",
                "HSE crystal requires load capacitors",
                "Include BOOT0 pull-down resistor",
                "Add reset button with pull-up"
            ],
            estimated_complexity=3
        )
    
    @staticmethod
    def _motor_stepper() -> PatternTemplate:
        """Stepper motor driver circuit"""
        return PatternTemplate(
            name="Stepper Motor Driver",
            description="DRV8825 stepper motor driver with current limiting",
            components=[
                ComponentSpec(
                    symbol="Driver_Motor:Pololu_Breakout_DRV8825",
                    footprint="Module:Pololu_Breakout-16_15.2x20.3mm",
                    value="DRV8825",
                    ref_prefix="A",
                    description="Stepper motor driver breakout"
                ),
                ComponentSpec(
                    symbol="Device:C",
                    footprint="Capacitor_SMD:C_1206_3216Metric", 
                    value="100uF",
                    ref_prefix="C",
                    description="Motor power decoupling"
                ),
                ComponentSpec(
                    symbol="Connector:Conn_01x04_Socket",
                    footprint="Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical",
                    value="MOTOR",
                    ref_prefix="J",
                    description="Stepper motor connector"
                )
            ],
            connections=[
                {"from": "A1.VMOT", "to": "12V_RAIL"},
                {"from": "A1.GND", "to": "GND"},  
                {"from": "A1.1A", "to": "J1.1"},
                {"from": "A1.1B", "to": "J1.2"}
            ],
            power_rails=["12V", "5V", "GND"],
            design_notes=[
                "Add large decoupling capacitor near motor power",
                "Use thick traces for motor current paths",
                "Include current limiting resistor adjustment", 
                "Consider heatsink for high-current applications"
            ],
            estimated_complexity=3
        )
    
    @staticmethod
    def _sensor_imu() -> PatternTemplate:
        """Standalone IMU sensor board"""
        return PatternTemplate(
            name="IMU Sensor Module", 
            description="MPU-6050 IMU with I2C interface and filtering",
            components=[
                ComponentSpec(
                    symbol="Sensor_Motion:MPU-6050",
                    footprint="Sensor_Motion:InvenSense_QFN-24_4x4mm_P0.5mm",
                    value="MPU-6050",
                    ref_prefix="U",
                    description="6-axis IMU sensor"
                ),
                ComponentSpec(
                    symbol="Device:C",
                    footprint="Capacitor_SMD:C_0603_1608Metric",
                    value="10nF",
                    ref_prefix="C", 
                    description="Power supply filter"
                ),
                ComponentSpec(
                    symbol="Connector:Conn_01x06_Pin",
                    footprint="Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
                    value="I2C_CONN",
                    ref_prefix="J",
                    description="I2C breakout connector"
                )
            ],
            connections=[
                {"from": "U1.VDD", "to": "J1.1"},
                {"from": "U1.GND", "to": "J1.2"},
                {"from": "U1.SCL", "to": "J1.3"}, 
                {"from": "U1.SDA", "to": "J1.4"}
            ],
            power_rails=["3V3", "GND"],
            design_notes=[
                "Add power supply filtering capacitor",
                "Keep crystal traces short",
                "Consider mounting orientation for application",
                "Add address selection jumper if needed"
            ],
            estimated_complexity=2
        )
    
    @staticmethod
    def _sensor_temp() -> PatternTemplate:
        """Temperature sensor circuit"""
        return PatternTemplate(
            name="Temperature Sensor",
            description="DS18B20 1-Wire temperature sensor",
            components=[
                ComponentSpec(
                    symbol="Sensor_Temperature:DS18B20U",
                    footprint="Package_TO_SOT_SMD:SOT-23",
                    value="DS18B20",
                    ref_prefix="U",
                    description="1-Wire temperature sensor"
                ),
                ComponentSpec(
                    symbol="Device:R", 
                    footprint="Resistor_SMD:R_0603_1608Metric",
                    value="4.7k",
                    ref_prefix="R",
                    description="1-Wire pull-up resistor"
                )
            ],
            connections=[
                {"from": "U1.VDD", "to": "3V3_RAIL"},
                {"from": "U1.GND", "to": "GND"},
                {"from": "U1.DQ", "to": "DATA_LINE"}
            ],
            power_rails=["3V3", "GND"],
            design_notes=[
                "Requires 4.7k pull-up resistor on data line",
                "Can be powered parasitically in some applications",
                "Multiple sensors can share same 1-Wire bus",
                "Consider ESD protection for external connections"
            ],
            estimated_complexity=1
        )
    
    @staticmethod
    def _led_neopixel() -> PatternTemplate:
        """NeoPixel LED strip driver with level shifter"""
        return PatternTemplate(
            name="NeoPixel LED Driver",
            description="Level shifter circuit for 3.3V to 5V NeoPixel control",
            components=[
                ComponentSpec(
                    symbol="74xx:74AHCT125",
                    footprint="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
                    value="74AHCT125",
                    ref_prefix="U",
                    description="3.3V to 5V level shifter"
                ),
                ComponentSpec(
                    symbol="Connector:Conn_01x03_Pin",
                    footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
                    value="LED_OUT",
                    ref_prefix="J",
                    description="NeoPixel strip connector"
                ),
                ComponentSpec(
                    symbol="Device:C",
                    footprint="Capacitor_SMD:C_1206_3216Metric",
                    value="470uF",
                    ref_prefix="C",
                    description="LED strip power smoothing"
                )
            ],
            connections=[
                {"from": "U1.VCC", "to": "5V_RAIL"},
                {"from": "U1.GND", "to": "GND"},
                {"from": "U1.1Y", "to": "J1.2"},  # Data out
                {"from": "J1.1", "to": "5V_RAIL"},  # LED power
                {"from": "J1.3", "to": "GND"}       # LED ground
            ],
            power_rails=["5V", "3V3", "GND"],
            design_notes=[
                "Level shifter required for 3.3V MCU to 5V LEDs",
                "Add large capacitor for LED current spikes", 
                "Consider current limiting for LED strips",
                "Use thick traces for LED power distribution"
            ],
            estimated_complexity=2
        )
    
    @staticmethod
    def _usb_power() -> PatternTemplate:
        """USB-C power delivery circuit""" 
        return PatternTemplate(
            name="USB-C Power Input",
            description="USB-C connector with basic power delivery",
            components=[
                ComponentSpec(
                    symbol="Connector:USB_C_Receptacle_USB2.0_16P",
                    footprint="Connector_USB:USB_C_Receptacle_GCT_USB4085",
                    value="USB-C",
                    ref_prefix="J",
                    description="USB-C power/data connector"
                ),
                ComponentSpec(
                    symbol="Device:R",
                    footprint="Resistor_SMD:R_0603_1608Metric",
                    value="5.1k",
                    ref_prefix="R", 
                    description="CC pull-down resistors"
                ),
                ComponentSpec(
                    symbol="Device:C",
                    footprint="Capacitor_SMD:C_1206_3216Metric", 
                    value="22uF",
                    ref_prefix="C",
                    description="VBUS filtering"
                )
            ],
            connections=[
                {"from": "J1.VBUS", "to": "5V_RAIL"},
                {"from": "J1.GND", "to": "GND"},
                {"from": "J1.CC1", "to": "R1.1"},
                {"from": "J1.CC2", "to": "R2.1"}
            ],
            power_rails=["5V", "GND"],
            design_notes=[
                "5.1k CC pull-down for 5V/3A power negotiation",
                "Add VBUS filtering capacitor",  
                "Consider ESD protection on data lines",
                "Use controlled impedance for high-speed signals"
            ],
            estimated_complexity=2
        )
    
    @staticmethod
    def _stm32_motor() -> PatternTemplate:
        """STM32 with motor control peripherals"""
        return PatternTemplate(
            name="STM32 Motor Control Board",
            description="STM32F4 with motor driver and encoder interfaces",
            components=[
                ComponentSpec(
                    symbol="MCU_ST_STM32F4:STM32F407VETx",
                    footprint="Package_QFP:LQFP-100_14x14mm_P0.5mm",
                    value="STM32F407VET6",
                    ref_prefix="U",
                    description="STM32F4 microcontroller"
                ),
                ComponentSpec(
                    symbol="Driver_Motor:Pololu_Breakout_DRV8825",
                    footprint="Module:Pololu_Breakout-16_15.2x20.3mm",
                    value="DRV8825",
                    ref_prefix="A",
                    description="Stepper motor driver"
                ),
                ComponentSpec(
                    symbol="Connector:Conn_01x05_Pin",
                    footprint="Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical",
                    value="ENCODER",
                    ref_prefix="J",
                    description="Encoder interface"
                )
            ],
            connections=[
                {"from": "U1.VDD", "to": "3V3_RAIL"},
                {"from": "A1.STEP", "to": "U1.PA8"},
                {"from": "A1.DIR", "to": "U1.PA9"},
                {"from": "J1.1", "to": "U1.PA0"},  # Encoder A
                {"from": "J1.2", "to": "U1.PA1"}   # Encoder B
            ],
            power_rails=["3V3", "12V", "GND"],
            design_notes=[
                "Use timer channels for encoder input",
                "Add current limiting resistor on motor driver",
                "Include protection diodes for motor",
                "Consider heat dissipation for motor driver"
            ],
            estimated_complexity=4
        )

    @staticmethod
    def _encoder_quad() -> PatternTemplate:
        """Quadrature encoder interface"""
        return PatternTemplate(
            name="Quadrature Encoder Interface",
            description="Quadrature encoder with pull-up resistors and filtering",
            components=[
                ComponentSpec(
                    symbol="Connector:Conn_01x05_Pin",
                    footprint="Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical", 
                    value="ENCODER",
                    ref_prefix="J",
                    description="Encoder connector (A, B, Z, VCC, GND)"
                ),
                ComponentSpec(
                    symbol="Device:R",
                    footprint="Resistor_SMD:R_0603_1608Metric",
                    value="10k",
                    ref_prefix="R",
                    description="Pull-up resistors"
                ),
                ComponentSpec(
                    symbol="Device:C",
                    footprint="Capacitor_SMD:C_0603_1608Metric",
                    value="100nF",
                    ref_prefix="C",
                    description="Signal filtering"
                )
            ],
            connections=[
                {"from": "J1.4", "to": "5V_RAIL"},  # Encoder VCC
                {"from": "J1.5", "to": "GND"},      # Encoder GND  
                {"from": "J1.1", "to": "R1.2"},    # A channel
                {"from": "J1.2", "to": "R2.2"},    # B channel
                {"from": "J1.3", "to": "R3.2"}     # Z index
            ],
            power_rails=["5V", "GND"],
            design_notes=[
                "Add pull-up resistors for open collector outputs",
                "Include filtering capacitors to reduce noise",
                "Use shielded cable for long encoder connections",
                "Consider Schmitt trigger inputs for noise immunity"  
            ],
            estimated_complexity=2
        )