#!/usr/bin/env python3
"""
Circuit-Synth New Project Setup Tool

Creates a complete circuit-synth project with:
- Claude AI agents registration (.claude/ directory)
- Example circuits (main.py + simple examples)
- Project README with usage guide
- KiCad installation verification
- Optional KiCad library setup
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text

# Import circuit-synth modules
from circuit_synth.claude_integration.agent_registry import register_circuit_agents
from circuit_synth.core.kicad_validator import validate_kicad_installation

console = Console()


def check_kicad_installation() -> Dict[str, Any]:
    """Check KiCad installation and return path info"""
    console.print("🔍 Checking KiCad installation...", style="yellow")

    try:
        result = validate_kicad_installation()
        if result.get("kicad_installed"):
            console.print("✅ KiCad found!", style="green")
            console.print(f"   Path: {result.get('kicad_path', 'Unknown')}")
            console.print(f"   Version: {result.get('version', 'Unknown')}")
            return result
        else:
            console.print("❌ KiCad not found", style="red")
            console.print("Please install KiCad 8.0+ from https://www.kicad.org/")
            return {"kicad_installed": False}
    except Exception as e:
        console.print(f"⚠️  Could not verify KiCad installation: {e}", style="yellow")
        return {"kicad_installed": False, "error": str(e)}


def get_kicad_library_preferences() -> List[str]:
    """Ask user about additional KiCad libraries they want to include"""
    console.print("\n📚 KiCad Library Setup", style="bold blue")

    common_libraries = [
        "Connector_Generic",
        "Device",
        "Diode",
        "LED",
        "Transistor_BJT",
        "Transistor_FET",
        "Amplifier_Operational",
        "MCU_ST_STM32F4",
        "MCU_Espressif",
        "RF_Module",
        "Regulator_Linear",
        "Sensor_Motion",
    ]

    console.print("Common useful libraries are included by default:")
    for lib in common_libraries[:6]:  # Show first 6
        console.print(f"  • {lib}")
    console.print("  • ... and more")

    if Confirm.ask("\nWould you like to add any additional KiCad symbol libraries?"):
        additional = Prompt.ask(
            "Enter library names (comma-separated, or press Enter to skip)"
        )
        if additional.strip():
            return [lib.strip() for lib in additional.split(",")]

    return []


def create_example_circuits(project_path: Path) -> None:
    """Create example circuit files"""
    examples_dir = project_path / "examples"
    examples_dir.mkdir(exist_ok=True)

    # Main circuit example
    main_circuit = '''#!/usr/bin/env python3
"""
Main Circuit Example - LED Blinker with STM32
Professional circuit design with hierarchical architecture
"""

from circuit_synth import *

@circuit(name="Power_Supply")
def power_supply_subcircuit():
    """USB-C to 3.3V power regulation subcircuit"""
    
    # Interface nets
    vbus_in = Net('VBUS_IN')
    vcc_3v3_out = Net('VCC_3V3_OUT') 
    gnd = Net('GND')
    
    # USB-C connector
    usb_conn = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P",
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle_Palconn_UTC16-G"
    )
    
    # 3.3V regulator
    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3", 
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    # Input/output capacitors
    cap_in = Component(symbol="Device:C", ref="C", value="10uF", 
                      footprint="Capacitor_SMD:C_0805_2012Metric")
    cap_out = Component(symbol="Device:C", ref="C", value="22uF",
                       footprint="Capacitor_SMD:C_0805_2012Metric")
    
    # Connections
    usb_conn["VBUS"] += vbus_in
    usb_conn["GND"] += gnd
    regulator["VIN"] += vbus_in  
    regulator["VOUT"] += vcc_3v3_out
    regulator["GND"] += gnd
    cap_in[1] += vbus_in
    cap_in[2] += gnd
    cap_out[1] += vcc_3v3_out
    cap_out[2] += gnd

@circuit(name="LED_Blinker")  
def led_blinker_subcircuit():
    """LED with current limiting resistor"""
    
    # Interface nets
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    led_control = Net('LED_CONTROL')
    
    # LED and resistor
    led = Component(symbol="Device:LED", ref="D", 
                   footprint="LED_SMD:LED_0805_2012Metric")
    resistor = Component(symbol="Device:R", ref="R", value="330",
                        footprint="Resistor_SMD:R_0805_2012Metric")
    
    # Connections  
    resistor[1] += vcc_3v3
    resistor[2] += led["A"]  # Anode
    led["K"] += led_control  # Cathode (controlled by MCU)

@circuit(name="STM32_LED_Blinker_Main")
def main_circuit():
    """Main hierarchical circuit - STM32 LED blinker"""
    
    # Create subcircuits
    power_supply = power_supply_subcircuit()
    led_blinker = led_blinker_subcircuit()
    
    # Add STM32 MCU (simplified for example)
    stm32 = Component(
        symbol="MCU_ST_STM32F4:STM32F401CCUx",
        ref="U", 
        footprint="Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm"
    )
    
    # Connect everything through shared nets
    power_vcc = Net('VCC_3V3')
    power_gnd = Net('GND') 
    gpio_out = Net('LED_CONTROL')
    
    # Connect power to MCU
    stm32["VDD"] += power_vcc
    stm32["VSS"] += power_gnd
    stm32["PA5"] += gpio_out  # GPIO output to control LED


if __name__ == "__main__":
    # Generate the hierarchical circuit
    circuit = main_circuit()
    
    # Create KiCad project with hierarchical sheets
    circuit.generate_kicad_project(
        project_name="STM32_LED_Blinker",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    
    print("✅ STM32 LED Blinker project generated!")
    print("📁 Check the STM32_LED_Blinker/ directory for KiCad files")
'''

    # Simple LED circuit
    simple_led = '''#!/usr/bin/env python3
"""
Simple LED Circuit - Hello World of Electronics
Basic LED with current limiting resistor
"""

from circuit_synth import *

@circuit
def hello_led():
    """Simple LED circuit with current limiting resistor"""
    
    # Components
    led = Component(
        symbol="Device:LED", 
        ref="D",
        footprint="LED_THT:LED_D5.0mm"
    )
    
    resistor = Component(
        symbol="Device:R",
        ref="R", 
        value="330",
        footprint="Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"
    )
    
    # Nets
    vcc = Net("VCC")
    gnd = Net("GND")
    led_anode = Net("LED_ANODE")
    
    # Connections
    resistor[1] += vcc
    resistor[2] += led_anode
    led["A"] += led_anode  # Anode
    led["K"] += gnd        # Cathode

if __name__ == "__main__":
    circuit = hello_led()
    circuit.generate_kicad_project("hello_led")
    print("✅ Hello LED circuit generated!")
'''

    # Voltage divider circuit
    voltage_divider = '''#!/usr/bin/env python3
"""
Voltage Divider Circuit - Basic Analog Design
Simple resistor voltage divider with optional simulation
"""

from circuit_synth import *

@circuit
def voltage_divider():
    """Voltage divider: 5V → 3.3V using resistors"""
    
    # Components - precision resistors for accurate division
    r1 = Component(symbol="Device:R", ref="R", value="1.7k", 
                  footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R", value="3.3k",
                  footprint="Resistor_SMD:R_0603_1608Metric") 
    
    # Nets
    vin = Net("VIN")      # 5V input
    vout = Net("VOUT")    # 3.3V output  
    gnd = Net("GND")      # Ground
    
    # Connections
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd
    
    # Optional: Add simulation analysis
    # To run simulation: circuit.simulator().operating_point()

if __name__ == "__main__":
    circuit = voltage_divider()
    circuit.generate_kicad_project("voltage_divider")
    print("✅ Voltage divider circuit generated!")
    print("🔬 Expected output: 3.28V (from 5V input)")
'''

    # Write example files
    with open(examples_dir / "main.py", "w") as f:
        f.write(main_circuit)

    with open(examples_dir / "simple_led.py", "w") as f:
        f.write(simple_led)

    with open(examples_dir / "voltage_divider.py", "w") as f:
        f.write(voltage_divider)

    console.print(f"✅ Created example circuits in {examples_dir}/", style="green")


def create_project_readme(
    project_path: Path, project_name: str, additional_libraries: List[str]
) -> None:
    """Create project README with circuit-synth usage guide"""

    readme_content = f"""# {project_name}

A circuit-synth project for professional circuit design with hierarchical architecture.

## 🚀 Quick Start

```bash
# Run the main hierarchical example
python examples/main.py

# Try simple examples
python examples/simple_led.py
python examples/voltage_divider.py
```

## 📁 Project Structure

```
{project_name}/
├── examples/              # Example circuits
│   ├── main.py           # Main hierarchical STM32 LED blinker
│   ├── simple_led.py     # Simple LED circuit
│   └── voltage_divider.py # Voltage divider example
├── .claude/              # AI agents for Claude Code
│   ├── agents/          # Specialized circuit design agents
│   └── mcp_settings.json # Claude Code configuration
└── README.md            # This file
```

## 🏗️ Circuit-Synth Basics

### **Hierarchical Design Philosophy**

Circuit-synth uses **hierarchical subcircuits** - each subcircuit is like a software function with single responsibility and clear interfaces:

```python
@circuit(name="Power_Supply")
def power_supply_subcircuit():
    \"\"\"Single responsibility: USB-C to 3.3V regulation\"\"\"
    # Define interface nets
    vbus_in = Net('VBUS_IN') 
    vcc_3v3_out = Net('VCC_3V3_OUT')
    gnd = Net('GND')
    # ... implement power regulation circuit
```

### **Basic Component Creation**

```python
# Create components with symbol, reference, and footprint
mcu = Component(
    symbol="MCU_ST_STM32F4:STM32F401CCUx",    # KiCad symbol
    ref="U",                                   # Reference prefix  
    footprint="Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm"
)

# Passive components with values
resistor = Component(symbol="Device:R", ref="R", value="330", 
                    footprint="Resistor_SMD:R_0805_2012Metric")
```

### **Net Connections**

```python
# Create nets for electrical connections
vcc = Net("VCC_3V3")
gnd = Net("GND")

# Connect components to nets
mcu["VDD"] += vcc      # Named pins
mcu["VSS"] += gnd
resistor[1] += vcc     # Numbered pins
```

### **Generate KiCad Projects**

```python
# Generate complete KiCad project
circuit = my_circuit()
circuit.generate_kicad_project(
    project_name="my_design",
    placement_algorithm="hierarchical",  # Professional layout
    generate_pcb=True                   # Include PCB file
)
```

## 🤖 AI-Powered Design with Claude Code

**Circuit-synth is an agent-first library** - designed to be used with and by AI agents for intelligent circuit design.

### **Available AI Agents**

This project includes specialized circuit design agents registered in `.claude/agents/`:

#### **🎯 circuit-synth Agent**
- **Expertise**: Circuit-synth code generation and KiCad integration
- **Usage**: `@Task(subagent_type="circuit-synth", description="Design power supply", prompt="Create 3.3V regulator circuit with USB-C input")`
- **Capabilities**: 
  - Generate production-ready circuit-synth code
  - KiCad symbol/footprint verification
  - JLCPCB component availability checking
  - Manufacturing-ready designs with verified components

#### **🔬 simulation-expert Agent**  
- **Expertise**: SPICE simulation and circuit validation
- **Usage**: `@Task(subagent_type="simulation-expert", description="Validate filter", prompt="Simulate and optimize this low-pass filter circuit")`
- **Capabilities**:
  - Professional SPICE analysis (DC, AC, transient)
  - Hierarchical circuit validation
  - Component value optimization
  - Performance analysis and reporting

### **Agent-First Design Philosophy**

**Natural Language → Working Code:** Describe what you want, get production-ready circuit-synth code.

```
👤 "Design a motor controller with STM32, 3 half-bridges, and CAN bus"

🤖 Claude (using circuit-synth agent):
   ✅ Searches components with real JLCPCB availability
   ✅ Generates hierarchical circuit-synth code
   ✅ Creates professional KiCad project
   ✅ Includes manufacturing data and alternatives
```

### **Component Intelligence Example**

```
👤 "Find STM32 with 3 SPIs available on JLCPCB"

🤖 **STM32G431CBT6** - Found matching component  
   📊 Stock: 83,737 units | Price: $2.50@100pcs
   ✅ 3 SPIs: SPI1, SPI2, SPI3
   
   # Ready-to-use circuit-synth code:
   mcu = Component(
       symbol="MCU_ST_STM32G4:STM32G431CBTx",
       ref="U", 
       footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
   )
```

### **Using Agents in Claude Code**

1. **Direct Agent Tasks**: Use `@Task()` with specific agents
2. **Natural Conversation**: Agents automatically activated based on context
3. **Multi-Agent Workflows**: Agents collaborate (circuit-synth → simulation-expert)

**Examples:**
```
# Design and validate workflow
👤 "Create and simulate a buck converter for 5V→3.3V@2A"

# Component search workflow  
👤 "Find a low-noise op-amp for audio applications, check JLCPCB stock"

# Hierarchical design workflow
👤 "Design ESP32 IoT sensor node with power management and wireless"
```

## 🔬 SPICE Simulation

Validate your designs with professional simulation:

```python
# Add to any circuit for simulation
circuit = my_circuit()
sim = circuit.simulator()

# DC analysis
result = sim.operating_point()
print(f"Output voltage: {{result.get_voltage('VOUT'):.3f}}V")

# AC frequency response  
ac_result = sim.ac_analysis(1, 100000)  # 1Hz to 100kHz
```

## 📚 KiCad Libraries

This project uses these KiCad symbol libraries:

**Standard Libraries:**
- Device (resistors, capacitors, LEDs)
- Connector_Generic (headers, connectors)
- MCU_ST_STM32F4 (STM32 microcontrollers)
- Regulator_Linear (voltage regulators)
- RF_Module (ESP32, wireless modules)

{f'''
**Additional Libraries:**
{chr(10).join(f"- {lib}" for lib in additional_libraries)}
''' if additional_libraries else ""}

## 🛠️ Development Workflow

1. **Design**: Create hierarchical subcircuits in Python
2. **Validate**: Use SPICE simulation for critical circuits  
3. **Generate**: Export to KiCad with proper hierarchical structure
4. **Manufacture**: Components verified for JLCPCB availability

## 📖 Documentation

- Circuit-Synth: https://circuit-synth.readthedocs.io
- KiCad: https://docs.kicad.org
- Component Search: Use Claude Code agents for intelligent component selection

## 🚀 Next Steps

1. Run the example circuits to familiarize yourself
2. Use Claude Code for AI-assisted circuit design
3. Create your own hierarchical subcircuits
4. Validate designs with SPICE simulation
5. Generate production-ready KiCad projects

**Happy circuit designing!** 🎛️
"""

    with open(project_path / "README.md", "w") as f:
        f.write(readme_content)

    console.print(f"✅ Created project README.md", style="green")


@click.command()
@click.argument("project_name", required=True)
@click.option("--skip-kicad-check", is_flag=True, help="Skip KiCad installation check")
@click.option("--minimal", is_flag=True, help="Create minimal project (no examples)")
def main(project_name: str, skip_kicad_check: bool, minimal: bool):
    """Create a new circuit-synth project with complete setup

    PROJECT_NAME: Name of the new project directory to create
    """

    console.print(
        Panel.fit(
            Text("🚀 Circuit-Synth New Project Setup", style="bold blue"), style="blue"
        )
    )

    # Create project directory
    project_path = Path.cwd() / project_name
    if project_path.exists():
        if not Confirm.ask(f"Directory '{project_name}' exists. Continue?"):
            console.print("❌ Aborted", style="red")
            sys.exit(1)
    else:
        project_path.mkdir(parents=True)
        console.print(f"📁 Created project directory: {project_path}", style="green")

    # Change to project directory
    os.chdir(project_path)

    # Step 1: Check KiCad installation
    if not skip_kicad_check:
        kicad_info = check_kicad_installation()
        if not kicad_info.get("kicad_installed"):
            if not Confirm.ask(
                "Continue without KiCad? (You'll need it later for opening projects)"
            ):
                console.print("❌ Aborted - Please install KiCad first", style="red")
                sys.exit(1)
    else:
        console.print("⏭️  Skipped KiCad check", style="yellow")

    # Step 2: Register Claude AI agents
    console.print("\n🤖 Setting up AI agents...", style="yellow")
    try:
        register_circuit_agents()
        console.print("✅ AI agents registered successfully", style="green")
    except Exception as e:
        console.print(f"⚠️  Could not register AI agents: {e}", style="yellow")

    # Step 3: Get library preferences
    additional_libraries = []
    if not minimal:
        additional_libraries = get_kicad_library_preferences()

    # Step 4: Create example circuits
    if not minimal:
        console.print("\n📝 Creating example circuits...", style="yellow")
        create_example_circuits(project_path)
    else:
        console.print("⏭️  Skipped example circuits (minimal mode)", style="yellow")

    # Step 5: Create project README
    console.print("\n📚 Creating project documentation...", style="yellow")
    create_project_readme(project_path, project_name, additional_libraries)

    # Success message
    console.print(
        Panel.fit(
            Text(
                f"✅ Project '{project_name}' created successfully!", style="bold green"
            )
            + Text(f"\n\n📁 Location: {project_path}")
            + Text(f"\n🚀 Get started: cd {project_name} && python examples/main.py")
            + Text(f"\n🤖 AI agents: Available in Claude Code")
            + Text(f"\n📖 Documentation: See README.md"),
            title="🎉 Success!",
            style="green",
        )
    )


if __name__ == "__main__":
    main()
