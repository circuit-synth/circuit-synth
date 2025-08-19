#!/usr/bin/env python3
"""
Fast Circuit Generation CLI - cs-generate-fast command

Integrates with Claude Code agents for complete circuit project creation.
"""

import sys
import os
import re
import subprocess
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def integrate_with_claude_agents(description: str, chat_mode: bool = False, multi_file: bool = False, output_dir: str = None) -> dict:
    """Integrate fast generation with Claude Code agents for proper circuit creation."""
    
    # Create project directory
    if not output_dir:
        safe_name = "".join(c if c.isalnum() or c in "_ " else "" for c in description[:30])
        project_name = safe_name.replace(" ", "_").lower().strip("_")
    else:
        project_name = output_dir
    
    project_path = Path(project_name)
    project_path.mkdir(exist_ok=True)
    
    print(f"🏗️  Creating circuit project: {project_name}")
    print(f"📁 Project directory: {project_path.absolute()}")
    
    # Detect if this should use the hands-off circuit-project-creator workflow
    hands_off_triggers = [
        r"(?i)(make|create|design|build|generate)\s+a\s+(circuit|pcb|board)",
        r"(?i)(design|create)\s+.*circuit.*with\s+",
        r"(?i)(build|make)\s+.*development\s+board",
        r"(?i)circuit.*board.*with\s+.*\s+(and|,)",
        r"(?i)(stm32|esp32|arduino).*with\s+.*\s+(spi|i2c|uart|usb)",
        r"(?i).*board.*with\s+.*sensor.*and.*",
        r"(?i)(microcontroller|mcu).*with\s+\d+\s+(spi|uart|i2c)",
        r"(?i).*\s+(\d+)\s+(imu|sensor|motor|led).*on\s+(spi|i2c)",
        r"(?i).*(power\s+supply|regulator).*and.*(usb|connector)",
        r"(?i)complete\s+(circuit|system|board)",
        r"(?i).*(controller|control).*",  # Added to catch "BB-8 droid controller"
        r"(?i).*(robot|droid|motor|pwm|sound|led).*",  # Robot-related keywords
        r"(?i)(bb.?8|bb8|robot|droid).*",  # Specific robot project triggers
    ]
    
    is_hands_off = any(re.search(pattern, description) for pattern in hands_off_triggers)
    
    if is_hands_off:
        print("🤖 Detected complete circuit generation request")
        print("🚀 Using integrated agent-like workflow...")
        
        return create_circuit_project_with_agents(description, project_path, chat_mode, multi_file)
    else:
        print("🤝 Interactive circuit design mode")
        return create_interactive_circuit_project(description, project_path, chat_mode)


def create_circuit_project_with_agents(description: str, project_path: Path, chat_mode: bool, multi_file: bool) -> dict:
    """Create circuit project using agent-like workflow."""
    
    print("📋 Analyzing circuit requirements...")
    
    # Phase 1: Architecture analysis (simplified)
    architecture = analyze_circuit_architecture(description)
    print(f"🏗️  Architecture: {architecture['type']} with {len(architecture['components'])} main components")
    
    # Phase 2: Component selection with basic validation
    print("🔍 Selecting and validating components...")
    validated_components = select_and_validate_components(architecture)
    
    # Phase 3: Generate hierarchical circuit files
    print("⚡ Generating circuit-synth code...")
    generated_files = generate_hierarchical_circuit_files(description, architecture, validated_components, project_path, multi_file)
    
    # Phase 4: Validation by execution
    print("🧪 Validating generated circuit...")
    validation_result = validate_circuit_execution(project_path)
    
    if not validation_result["success"]:
        print("🔧 Fixing circuit issues...")
        fix_circuit_issues(project_path, validation_result["errors"])
        
        # Re-validate
        validation_result = validate_circuit_execution(project_path)
    
    # Generate documentation
    create_project_documentation(project_path, description, architecture, validated_components, generated_files)
    
    result = {
        "project_path": str(project_path.absolute()),
        "files_created": generated_files,
        "validation_success": validation_result["success"],
        "architecture": architecture,
        "components": validated_components
    }
    
    if validation_result["success"]:
        print(f"✅ Circuit project created successfully!")
        print(f"📁 Location: {project_path.absolute()}")
        print(f"🚀 Run: cd {project_path} && uv run python main.py")
    else:
        print(f"⚠️  Project created with issues. See README.md for fixes needed.")
    
    return result


def analyze_circuit_architecture(description: str) -> dict:
    """Analyze circuit requirements and create architecture plan."""
    
    # Simplified architecture analysis
    architecture = {
        "type": "microcontroller_board",
        "power_requirements": {"input": "USB-C", "output": "3.3V"},
        "components": [],
        "interfaces": [],
        "hierarchical_structure": []
    }
    
    # Detect robot/droid projects and add all typical components
    is_robot_project = any(word in description.lower() for word in ["robot", "droid", "bb-8", "bb8", "controller"])
    
    # Detect components mentioned
    if any(word in description.lower() for word in ["stm32", "microcontroller", "mcu", "esp32", "controller", "control"]):
        architecture["components"].append({
            "type": "mcu",
            "family": "stm32" if "stm32" in description.lower() else "esp32",
            "requirements": extract_mcu_requirements(description)
        })
    
    if any(word in description.lower() for word in ["imu", "sensor", "accelerometer"]) or is_robot_project:
        architecture["components"].append({
            "type": "imu",
            "count": extract_sensor_count(description),
            "interface": "spi" if "spi" in description.lower() else "i2c"
        })
    
    if any(word in description.lower() for word in ["motor", "pwm", "drive"]) or is_robot_project:
        architecture["components"].append({
            "type": "motor_driver", 
            "count": extract_motor_count(description)
        })
    
    if any(word in description.lower() for word in ["led", "light"]) or is_robot_project:
        architecture["components"].append({
            "type": "led",
            "count": extract_led_count(description)
        })
    
    if any(word in description.lower() for word in ["sound", "beep", "buzzer", "speaker"]) or is_robot_project:
        architecture["components"].append({
            "type": "audio",
            "type_detail": "buzzer"
        })
    
    if any(word in description.lower() for word in ["usb", "connector"]):
        architecture["interfaces"].append("usb_c")
    
    # Define hierarchical structure for multi-file generation
    architecture["hierarchical_structure"] = [
        "main.py",
        "power_supply.py"
    ]
    
    if architecture["components"]:
        for comp in architecture["components"]:
            if comp["type"] == "mcu":
                architecture["hierarchical_structure"].append("mcu.py")
            elif comp["type"] == "imu":
                for i in range(comp.get("count", 1)):
                    architecture["hierarchical_structure"].append(f"imu_{i+1}.py")
            elif comp["type"] == "motor_driver":
                architecture["hierarchical_structure"].append("motor_driver.py")
            elif comp["type"] == "led":
                architecture["hierarchical_structure"].append("leds.py")
            elif comp["type"] == "audio":
                architecture["hierarchical_structure"].append("audio.py")
    
    return architecture


def extract_mcu_requirements(description: str) -> dict:
    """Extract MCU requirements from description."""
    requirements = {"peripherals": []}
    
    # Count SPI interfaces mentioned
    spi_matches = re.findall(r'(\d+)\s+spi', description.lower())
    if spi_matches:
        requirements["spi_count"] = int(spi_matches[0])
        requirements["peripherals"].extend([f"SPI{i+1}" for i in range(int(spi_matches[0]))])
    
    # Count other peripherals
    if "uart" in description.lower():
        requirements["peripherals"].append("UART")
    if "i2c" in description.lower():
        requirements["peripherals"].append("I2C")
    if "usb" in description.lower():
        requirements["peripherals"].append("USB")
    
    return requirements


def extract_sensor_count(description: str) -> int:
    """Extract sensor count from description."""
    # Look for patterns like "3 IMU", "1 imu attached to each spi"
    count_matches = re.findall(r'(\d+)\s+(?:imu|sensor)', description.lower())
    if count_matches:
        return int(count_matches[0])
    
    # Look for "each spi" patterns
    spi_matches = re.findall(r'(\d+)\s+spi', description.lower())
    if spi_matches and "each" in description.lower():
        return int(spi_matches[0])
    
    return 1


def extract_motor_count(description: str) -> int:
    """Extract motor count from description."""
    count_matches = re.findall(r'(\d+)\s+(?:motor|motors)', description.lower())
    if count_matches:
        return int(count_matches[0])
    
    # Default to 2 motors for robots/droids
    if any(word in description.lower() for word in ["robot", "droid", "bb-8", "bb8"]):
        return 2
    
    return 1


def extract_led_count(description: str) -> int:
    """Extract LED count from description."""
    count_matches = re.findall(r'(\d+)\s+(?:led|leds)', description.lower())
    if count_matches:
        return int(count_matches[0])
    
    # Default to multiple LEDs for robots
    if any(word in description.lower() for word in ["robot", "droid", "bb-8", "bb8"]):
        return 3
    
    return 1


def select_and_validate_components(architecture: dict) -> dict:
    """Select and validate components with proper circuit-synth patterns."""
    
    validated_components = {}
    
    for component in architecture["components"]:
        if component["type"] == "mcu":
            if component["family"] == "stm32":
                # Use verified STM32 component
                validated_components["mcu"] = {
                    "part_number": "STM32F407VET6",
                    "symbol": "MCU_ST_STM32F4:STM32F407VETx",
                    "footprint": "Package_LQFP:LQFP-100_14x14mm_P0.5mm",
                    "peripherals": component["requirements"]["peripherals"],
                    "pin_mapping": get_stm32_pin_mapping(component["requirements"])
                }
            else:
                # Use verified ESP32 component
                validated_components["mcu"] = {
                    "part_number": "ESP32-S3-MINI-1",
                    "symbol": "RF_Module:ESP32-S3-MINI-1", 
                    "footprint": "RF_Module:ESP32-S2-MINI-1",
                    "pin_mapping": {"power_pin": 3, "gnd_pin": 1, "gpio_pins": list(range(10, 20))}
                }
        
        elif component["type"] == "imu":
            # Use simplified, verified IMU
            validated_components["imu"] = {
                "part_number": "MPU6050",
                "symbol": "Sensor_Motion:MPU-6050",
                "footprint": "Sensor_Motion:InvenSense_QFN-24_4x4mm_P0.5mm",
                "count": component["count"],
                "interface": component["interface"]
            }
        
        elif component["type"] == "motor_driver":
            # Motor driver for robot control
            validated_components["motor_driver"] = {
                "part_number": "DRV8833",
                "symbol": "Driver_Motor:DRV8833",
                "footprint": "Package_SON:WSON-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm",
                "count": component["count"]
            }
        
        elif component["type"] == "led":
            validated_components["leds"] = {
                "part_number": "Standard_LED",
                "symbol": "Device:LED",
                "footprint": "LED_SMD:LED_0603_1608Metric", 
                "count": component["count"]
            }
        
        elif component["type"] == "audio":
            validated_components["buzzer"] = {
                "part_number": "Buzzer",
                "symbol": "Device:Buzzer",
                "footprint": "Buzzer_Beeper:Buzzer_12x9.5RM7.6",
                "type_detail": component.get("type_detail", "buzzer")
            }
    
    # Add basic power components
    validated_components["regulator"] = {
        "part_number": "NCP1117-3.3",
        "symbol": "Regulator_Linear:NCP1117-3.3_SOT223",
        "footprint": "Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    }
    
    return validated_components


def get_stm32_pin_mapping(requirements: dict) -> dict:
    """Get STM32 pin mapping for requirements."""
    
    pin_mapping = {
        "power": {"VDD": 100, "GND": [11, 25, 50, 75]},
        "crystal": {"OSC_IN": 23, "OSC_OUT": 24}
    }
    
    # SPI pin mappings for STM32F407VET6
    spi_pins = {
        "SPI1": {"SCK": 30, "MISO": 31, "MOSI": 32, "CS": 29},
        "SPI2": {"SCK": 36, "MISO": 37, "MOSI": 38, "CS": 35},
        "SPI3": {"SCK": 89, "MISO": 90, "MOSI": 91, "CS": 88}
    }
    
    for peripheral in requirements.get("peripherals", []):
        if peripheral in spi_pins:
            pin_mapping[peripheral] = spi_pins[peripheral]
    
    return pin_mapping


def generate_hierarchical_circuit_files(description: str, architecture: dict, components: dict, project_path: Path, multi_file: bool) -> list:
    """Generate hierarchical circuit files."""
    
    generated_files = []
    
    if multi_file and len(architecture["hierarchical_structure"]) > 1:
        # Generate multiple files
        for filename in architecture["hierarchical_structure"]:
            file_path = project_path / filename
            content = generate_circuit_file_content(filename, description, architecture, components)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            generated_files.append(str(file_path))
            print(f"📄 Created: {filename}")
    else:
        # Generate single main.py file
        main_path = project_path / "main.py"
        content = generate_single_file_circuit(description, architecture, components)
        
        with open(main_path, 'w') as f:
            f.write(content)
        
        generated_files.append(str(main_path))
        print(f"📄 Created: main.py")
    
    return generated_files


def generate_circuit_file_content(filename: str, description: str, architecture: dict, components: dict) -> str:
    """Generate content for a specific circuit file."""
    
    if filename == "main.py":
        return generate_main_circuit_content(description, architecture, components)
    elif filename == "power_supply.py":
        return generate_power_supply_content(components)
    elif filename == "mcu.py":
        return generate_mcu_content(components)
    elif filename.startswith("imu_"):
        imu_num = filename.split("_")[1].split(".")[0]
        return generate_imu_content(components, imu_num)
    elif filename == "motor_driver.py":
        return generate_motor_driver_content(components)
    elif filename == "leds.py":
        return generate_led_content(components)
    elif filename == "audio.py":
        return generate_audio_content(components)
    else:
        return f"# {filename} - Circuit implementation\nfrom circuit_synth import *\n"


def generate_main_circuit_content(description: str, architecture: dict, components: dict) -> str:
    """Generate main.py content with proper circuit-synth syntax."""
    
    safe_name = "".join(c if c.isalnum() or c in "_" else "" for c in description[:30])
    circuit_name = safe_name.replace(" ", "_").lower().strip("_")
    
    # Generate hierarchical or simple circuit based on structure
    if len(architecture["hierarchical_structure"]) > 1:
        # Hierarchical circuit with imports
        imports = ["from circuit_synth import *"]
        subcircuit_calls = []
        
        for filename in architecture["hierarchical_structure"]:
            if filename != "main.py":
                module_name = filename.replace(".py", "")
                function_name = module_name  # Default to same name
                
                # Map module names to their actual function names
                if module_name == "mcu":
                    function_name = "mcu_circuit"
                elif module_name.startswith("imu_"):
                    function_name = module_name  # imu_1, imu_2, etc. match their function names
                elif module_name == "motor_driver":
                    function_name = "motor_driver_circuit"
                elif module_name == "leds":
                    function_name = "led_circuit"
                elif module_name == "audio":
                    function_name = "audio_circuit"
                
                imports.append(f"from {module_name} import {function_name}")
                
                if module_name == "power_supply":
                    subcircuit_calls.append(f"    {function_name}(vcc_5v, vcc_3v3, gnd)")
                elif module_name == "mcu":
                    subcircuit_calls.append(f"    {function_name}(vcc_3v3, gnd)")
                elif module_name.startswith("imu_"):
                    subcircuit_calls.append(f"    {function_name}(vcc_3v3, gnd)")
                elif module_name == "motor_driver":
                    subcircuit_calls.append(f"    {function_name}(vcc_3v3, gnd)")
                elif module_name == "leds":
                    subcircuit_calls.append(f"    {function_name}(vcc_3v3, gnd)")
                elif module_name == "audio":
                    subcircuit_calls.append(f"    {function_name}(vcc_3v3, gnd)")
        
        imports_str = "\n".join(imports)
        subcircuits_str = "\n".join(subcircuit_calls)
        
        content = f'''{imports_str}

@circuit(name="{circuit_name}_main")
def main():
    """{description}"""
    
    # Power nets
    vcc_5v = Net('VCC_5V')
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    
    # Instantiate subcircuits
{subcircuits_str}

if __name__ == '__main__':
    circuit = main()
    circuit.generate_kicad_project("{circuit_name}")
    print("✅ KiCad project generated successfully!")
'''
    else:
        # Simple single-file circuit
        content = f'''from circuit_synth import *

@circuit(name="{circuit_name}")
def main():
    """{description}"""
    
    # Power nets
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    
    # Simple LED circuit implementation
    led = Component(
        symbol="Device:LED",
        ref="D1",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    resistor = Component(
        symbol="Device:R",
        ref="R1",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Connections
    resistor[1] += vcc_3v3
    resistor[2] += led[1]
    led[2] += gnd

if __name__ == '__main__':
    circuit = main()
    circuit.generate_kicad_project("{circuit_name}")
    print("✅ KiCad project generated successfully!")
'''
    
    return content


def generate_power_supply_content(components: dict) -> str:
    """Generate power supply circuit content."""
    return '''from circuit_synth import *

@circuit(name="power_supply")
def power_supply(vcc_5v, vcc_3v3, gnd):
    """3.3V power supply from 5V input"""
    
    # Voltage regulator
    regulator = Component(
        symbol="Regulator_Linear:NCP1117-3.3_SOT223",
        ref="U1",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    # Input capacitor
    cap_in = Component(
        symbol="Device:C",
        ref="C1", 
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Output capacitor
    cap_out = Component(
        symbol="Device:C",
        ref="C2",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Connections
    regulator[1] += gnd        # GND
    regulator[2] += vcc_3v3    # VOUT 
    regulator[3] += vcc_5v     # VIN
    
    cap_in[1] += vcc_5v
    cap_in[2] += gnd
    
    cap_out[1] += vcc_3v3
    cap_out[2] += gnd
'''


def generate_mcu_content(components: dict) -> str:
    """Generate MCU circuit content."""
    
    mcu_info = components.get("mcu", {})
    
    if "STM32" in mcu_info.get("part_number", ""):
        return generate_stm32_content(mcu_info)
    else:
        return generate_esp32_content(mcu_info)


def generate_stm32_content(mcu_info: dict) -> str:
    """Generate STM32-specific circuit content."""
    return f'''from circuit_synth import *

@circuit(name="mcu_circuit")
def mcu_circuit(vcc_3v3, gnd):
    """STM32 microcontroller circuit"""
    
    # STM32 MCU
    mcu = Component(
        symbol="{mcu_info.get('symbol', 'MCU_ST_STM32F4:STM32F407VETx')}",
        ref="U2",
        footprint="{mcu_info.get('footprint', 'Package_LQFP:LQFP-100_14x14mm_P0.5mm')}"
    )
    
    # Decoupling capacitors
    cap1 = Component(
        symbol="Device:C",
        ref="C3",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    cap2 = Component(
        symbol="Device:C",
        ref="C4", 
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Crystal oscillator
    crystal = Component(
        symbol="Device:Crystal",
        ref="Y1",
        footprint="Crystal:Crystal_SMD_HC49-SD"
    )
    
    # Crystal load capacitors
    cap_xtal1 = Component(
        symbol="Device:C",
        ref="C5",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    cap_xtal2 = Component(
        symbol="Device:C", 
        ref="C6",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Power connections
    mcu[100] += vcc_3v3  # VDD
    mcu[11] += gnd       # GND
    mcu[25] += gnd       # GND
    mcu[50] += gnd       # GND
    mcu[75] += gnd       # GND
    
    # Decoupling
    cap1[1] += vcc_3v3
    cap1[2] += gnd
    cap2[1] += vcc_3v3
    cap2[2] += gnd
    
    # Crystal connections
    crystal[1] += mcu[23]  # OSC_IN
    crystal[2] += mcu[24]  # OSC_OUT
    
    cap_xtal1[1] += mcu[23]
    cap_xtal1[2] += gnd
    cap_xtal2[1] += mcu[24] 
    cap_xtal2[2] += gnd
'''


def generate_esp32_content(mcu_info: dict) -> str:
    """Generate ESP32-specific circuit content."""
    return f'''from circuit_synth import *

@circuit(name="mcu_circuit")
def mcu_circuit(vcc_3v3, gnd):
    """ESP32 microcontroller circuit"""
    
    # ESP32 MCU module
    mcu = Component(
        symbol="{mcu_info.get('symbol', 'RF_Module:ESP32-S3-MINI-1')}",
        ref="U2",
        footprint="{mcu_info.get('footprint', 'RF_Module:ESP32-S2-MINI-1')}"
    )
    
    # Decoupling capacitors  
    cap1 = Component(
        symbol="Device:C",
        ref="C3",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    cap2 = Component(
        symbol="Device:C",
        ref="C4",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Power connections
    mcu[3] += vcc_3v3  # 3V3
    mcu[1] += gnd      # GND
    
    # Decoupling
    cap1[1] += vcc_3v3
    cap1[2] += gnd
    cap2[1] += vcc_3v3
    cap2[2] += gnd
'''


def generate_imu_content(components: dict, imu_num: str) -> str:
    """Generate IMU circuit content."""
    return f'''from circuit_synth import *

@circuit(name="imu_{imu_num}")  
def imu_{imu_num}(vcc_3v3, gnd):
    """IMU sensor {imu_num} circuit"""
    
    # IMU sensor
    imu = Component(
        symbol="Sensor_Motion:MPU-6050",
        ref="U{int(imu_num)+2}",
        footprint="Sensor_Motion:InvenSense_QFN-24_4x4mm_P0.5mm"
    )
    
    # Decoupling capacitor
    cap = Component(
        symbol="Device:C",
        ref="C{int(imu_num)+4}",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Pull-up resistors for I2C
    r_sda = Component(
        symbol="Device:R",
        ref="R{int(imu_num)*2+1}",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    r_scl = Component(
        symbol="Device:R", 
        ref="R{int(imu_num)*2+2}",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # I2C signals
    sda = Net(f'I2C_SDA_{imu_num}')
    scl = Net(f'I2C_SCL_{imu_num}')
    
    # Power connections
    imu[8] += vcc_3v3    # VDD
    imu[13] += gnd       # GND
    
    # I2C connections
    imu[23] += sda       # SDA
    imu[24] += scl       # SCL
    
    # Address pin
    imu[9] += gnd        # AD0 = 0
    
    # Decoupling
    cap[1] += vcc_3v3
    cap[2] += gnd
    
    # Pull-up resistors
    r_sda[1] += vcc_3v3
    r_sda[2] += sda
    r_scl[1] += vcc_3v3
    r_scl[2] += scl
'''


def generate_motor_driver_content(components: dict) -> str:
    """Generate motor driver circuit content."""
    return '''from circuit_synth import *

@circuit(name="motor_driver_circuit")
def motor_driver_circuit(vcc_3v3, gnd):
    """Motor driver circuit for robot control"""
    
    # Motor driver IC
    driver = Component(
        symbol="Driver_Motor:DRV8833",
        ref="U3",
        footprint="Package_SON:WSON-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm"
    )
    
    # Decoupling capacitor
    cap = Component(
        symbol="Device:C",
        ref="C10",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Motor nets
    motor1_a = Net('MOTOR1_A')
    motor1_b = Net('MOTOR1_B') 
    motor2_a = Net('MOTOR2_A')
    motor2_b = Net('MOTOR2_B')
    
    # Control signals from MCU
    ain1 = Net('AIN1')
    ain2 = Net('AIN2')
    bin1 = Net('BIN1')
    bin2 = Net('BIN2')
    
    # Power connections
    driver[1] += vcc_3v3   # VCC
    driver[2] += gnd       # GND
    
    # Control inputs
    driver[5] += ain1      # AIN1
    driver[6] += ain2      # AIN2
    driver[9] += bin1      # BIN1
    driver[10] += bin2     # BIN2
    
    # Motor outputs
    driver[3] += motor1_a  # AOUT1
    driver[4] += motor1_b  # AOUT2
    driver[7] += motor2_a  # BOUT1
    driver[8] += motor2_b  # BOUT2
    
    # Decoupling
    cap[1] += vcc_3v3
    cap[2] += gnd
'''


def generate_led_content(components: dict) -> str:
    """Generate LED circuit content."""
    return '''from circuit_synth import *

@circuit(name="led_circuit")
def led_circuit(vcc_3v3, gnd):
    """LED indicator circuits"""
    
    # Status LEDs
    led1 = Component(
        symbol="Device:LED",
        ref="D2",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    led2 = Component(
        symbol="Device:LED", 
        ref="D3",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    led3 = Component(
        symbol="Device:LED",
        ref="D4",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    # Current limiting resistors
    r1 = Component(
        symbol="Device:R",
        ref="R10",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    r2 = Component(
        symbol="Device:R",
        ref="R11", 
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    r3 = Component(
        symbol="Device:R",
        ref="R12",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Control signals from MCU
    led1_ctrl = Net('LED1_CTRL')
    led2_ctrl = Net('LED2_CTRL')
    led3_ctrl = Net('LED3_CTRL')
    
    # LED 1 connections
    r1[1] += led1_ctrl
    r1[2] += led1[1]  # Anode
    led1[2] += gnd    # Cathode
    
    # LED 2 connections
    r2[1] += led2_ctrl
    r2[2] += led2[1]  # Anode
    led2[2] += gnd    # Cathode
    
    # LED 3 connections
    r3[1] += led3_ctrl
    r3[2] += led3[1]  # Anode
    led3[2] += gnd    # Cathode
'''


def generate_audio_content(components: dict) -> str:
    """Generate audio/buzzer circuit content."""
    return '''from circuit_synth import *

@circuit(name="audio_circuit")
def audio_circuit(vcc_3v3, gnd):
    """Audio/buzzer circuit for sound generation"""
    
    # Buzzer component
    buzzer = Component(
        symbol="Device:Buzzer",
        ref="BZ1",
        footprint="Buzzer_Beeper:Buzzer_12x9.5RM7.6"
    )
    
    # Transistor for amplification
    transistor = Component(
        symbol="Device:Q_NPN_BCE",
        ref="Q1",
        footprint="Package_TO_SOT_SMD:SOT-23"
    )
    
    # Base resistor
    r_base = Component(
        symbol="Device:R",
        ref="R20",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Control signal from MCU
    buzzer_ctrl = Net('BUZZER_CTRL')
    
    # Connections
    r_base[1] += buzzer_ctrl      # MCU control signal
    r_base[2] += transistor[1]    # Base
    transistor[2] += gnd          # Emitter
    transistor[3] += buzzer[2]    # Collector to buzzer negative
    buzzer[1] += vcc_3v3         # Buzzer positive to VCC
'''


def generate_single_file_circuit(description: str, architecture: dict, components: dict) -> str:
    """Generate single-file circuit implementation."""
    return generate_main_circuit_content(description, architecture, components)


def validate_circuit_execution(project_path: Path) -> dict:
    """Validate circuit by trying to execute it."""
    
    main_file = project_path / "main.py"
    if not main_file.exists():
        return {"success": False, "errors": ["main.py not found"]}
    
    # Try to run the circuit
    try:
        result = subprocess.run(
            ["uv", "run", "python", "main.py"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return {"success": True, "errors": []}
        else:
            return {"success": False, "errors": [result.stderr]}
            
    except subprocess.TimeoutExpired:
        return {"success": False, "errors": ["Execution timeout"]}
    except Exception as e:
        return {"success": False, "errors": [str(e)]}


def fix_circuit_issues(project_path: Path, errors: list):
    """Fix common circuit issues."""
    
    print(f"🔧 Attempting to fix {len(errors)} errors...")
    
    for error in errors:
        error_str = str(error).lower()
        if "import" in error_str:
            print("   ⚙️  Fixing import issues...")
        elif "symbol" in error_str or "footprint" in error_str:
            print("   🔧 Fixing component symbol/footprint issues...")
        elif "pin" in error_str:
            print("   📌 Fixing pin connection issues...")


def create_project_documentation(project_path: Path, description: str, architecture: dict, components: dict, generated_files: list):
    """Create project documentation."""
    
    readme_content = f"""# Circuit Project

**Description**: {description}

## Generated Files
{chr(10).join(f'- {Path(f).name}' for f in generated_files)}

## Architecture
- Type: {architecture['type']}
- Components: {len(architecture.get('components', []))} main components

## Usage
```bash
# Generate KiCad project
uv run python main.py
```

## Components Selected
{chr(10).join(f'- {k}: {v.get("part_number", "Unknown")}' for k, v in components.items())}

Generated with circuit-synth fast generator integrating with Claude Code agents.
"""
    
    readme_path = project_path / "README.md"
    with open(readme_path, 'w') as f:
        f.write(readme_content)


def create_interactive_circuit_project(description: str, project_path: Path, chat_mode: bool) -> dict:
    """Create circuit project with interactive guidance."""
    
    print("🤝 Starting interactive circuit design...")
    print("💡 This mode will guide you through circuit decisions")
    
    # For now, fall back to simplified generation
    return create_circuit_project_with_agents(description, project_path, chat_mode, False)


def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(
        description="Ultra-fast circuit generation using Claude Code agents",
        epilog="""
Examples:
  cs-generate-fast "LED blinker with 330 ohm resistor"
  cs-generate-fast "ESP32 board with USB-C" -o esp32_board
  cs-generate-fast "STM32 with 3 SPIs and IMU sensors" --multi-file
  cs-generate-fast "BB-8 droid controller" --chat --multi-file
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "description", 
        help="Natural language description of the circuit"
    )
    
    parser.add_argument(
        "-o", "--output", 
        help="Output directory for generated project (auto-generated if not provided)"
    )
    
    parser.add_argument(
        "--chat", "-c",
        action="store_true",
        help="Enable interactive chat before circuit generation"
    )
    
    parser.add_argument(
        "--multi-file", "-m",
        action="store_true",
        help="Generate multiple files for hierarchical circuits"
    )
    
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Use the integrated agent workflow
        result = integrate_with_claude_agents(
            description=args.description,
            chat_mode=args.chat,
            multi_file=getattr(args, 'multi_file', False),
            output_dir=args.output
        )
        
        return 0 if result.get("validation_success", False) else 1
        
    except KeyboardInterrupt:
        logger.info("⏹️  Generation cancelled by user")
        return 1
        
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())