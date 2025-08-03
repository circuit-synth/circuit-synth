#!/usr/bin/env python3
"""
Circuit-Synth New PCB Setup Tool

Creates a complete PCB development environment with:
- Circuit-synth Python examples
- Memory-bank system for automatic documentation
- Claude AI agent for PCB-specific assistance
- Comprehensive CLAUDE.md with all commands
- No separate KiCad directory (files generated in circuit-synth)
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Import circuit-synth modules
from circuit_synth.memory_bank import MemoryBankManager

console = Console()


def create_full_hierarchical_examples(pcb_path: Path, pcb_name: str) -> None:
    """Create full hierarchical ESP32-C6 development board example like example_project."""
    circuit_synth_dir = pcb_path / "circuit-synth"
    circuit_synth_dir.mkdir(exist_ok=True)

    # Main circuit - only nets and subcircuit calls (like example_project)
    main_circuit = f'''#!/usr/bin/env python3
"""
{pcb_name} - ESP32-C6 Development Board
Complete development board with USB-C, power regulation, and debug interface
"""

from circuit_synth import *
from usb import usb_port
from power_supply import power_supply
from debug_header import debug_header
from led_blinker import led_blinker
from esp32c6 import esp32c6

@circuit(name="{pcb_name.replace(' ', '_')}")
def main_circuit():
    """Main circuit - ONLY nets and subcircuit connections"""
    
    # Create shared nets between subcircuits (ONLY nets - no components here)
    vbus = Net('VBUS')
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    usb_dp = Net('USB_DP')
    usb_dm = Net('USB_DM')
    
    # Create all circuits with shared nets
    usb_port_circuit = usb_port(vbus, gnd, usb_dp, usb_dm)
    power_supply_circuit = power_supply(vbus, vcc_3v3, gnd)
    esp32_circuit = esp32c6(vcc_3v3, gnd, usb_dp, usb_dm)

if __name__ == "__main__":
    print("🚀 Starting {pcb_name} generation...")
    
    # Generate the complete hierarchical circuit
    print("📋 Creating circuit...")
    circuit = main_circuit()
    
    # Generate KiCad project
    print("🏗️  Generating KiCad project...")
    circuit.generate_kicad_project(
        project_name="{pcb_name.replace(' ', '_')}",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    
    print("")
    print("✅ {pcb_name} project generated!")
    print(f"📁 Check the {pcb_name.replace(' ', '_')}/ directory for KiCad files")
    print("")
    print("🏗️  Generated circuits:")
    print("   • USB-C port with CC resistors and ESD protection")
    print("   • 5V to 3.3V power regulation")
    print("   • ESP32-C6 microcontroller with support circuits")
    print("   • Debug header for programming")  
    print("   • Status LED with current limiting")
    print("")
    print("🎯 Ready for professional PCB manufacturing!")
    print(f"💡 Open {pcb_name.replace(' ', '_')}.kicad_pro in KiCad to see the design!")
'''

    # USB circuit
    usb_circuit = '''#!/usr/bin/env python3
"""
USB-C Circuit - Professional USB-C implementation with ESD protection
Includes CC resistors, ESD protection, and shield grounding
"""
from circuit_synth import *

@circuit(name="USB_Port")
def usb_port(vbus_out, gnd, usb_dp, usb_dm):
    """USB-C port with CC resistors, ESD protection, and proper grounding"""
    
    # USB-C connector
    usb_conn = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P",
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal"
    )
    
    # CC pull-down resistors (5.1k for UFP device)
    cc1_resistor = Component(symbol="Device:R", ref="R", value="5.1k",
                            footprint="Resistor_SMD:R_0603_1608Metric")
    cc2_resistor = Component(symbol="Device:R", ref="R", value="5.1k", 
                            footprint="Resistor_SMD:R_0603_1608Metric")
    
    # ESD protection diodes for data lines
    esd_dp = Component(symbol="Diode:ESD5Zxx", ref="D",
                      footprint="Diode_SMD:D_SOD-523")
    esd_dm = Component(symbol="Diode:ESD5Zxx", ref="D",
                      footprint="Diode_SMD:D_SOD-523")
    
    # USB decoupling capacitor
    cap_usb = Component(symbol="Device:C", ref="C", value="10uF",
                       footprint="Capacitor_SMD:C_0805_2012Metric")
    
    # USB-C connections
    usb_conn["VBUS"] += vbus_out
    usb_conn["GND"] += gnd
    usb_conn["SHIELD"] += gnd  # Ground the shield
    usb_conn["D+"] += usb_dp
    usb_conn["D-"] += usb_dm
    
    # CC resistors to ground
    usb_conn["CC1"] += cc1_resistor[1]
    cc1_resistor[2] += gnd
    usb_conn["CC2"] += cc2_resistor[1] 
    cc2_resistor[2] += gnd
    
    # ESD protection (connector side)
    esd_dp[1] += usb_dp
    esd_dp[2] += gnd
    esd_dm[1] += usb_dm
    esd_dm[2] += gnd
    
    # USB decoupling capacitor connections
    cap_usb[1] += vbus_out
    cap_usb[2] += gnd

'''

    # Power supply circuit
    power_supply_circuit = '''#!/usr/bin/env python3
"""
Power Supply Circuit - 5V to 3.3V regulation
Clean power regulation from USB-C VBUS to regulated 3.3V
"""

from circuit_synth import *

@circuit(name="Power_Supply")
def power_supply(vbus_in, vcc_3v3_out, gnd):
    """5V to 3.3V power regulation subcircuit"""
    
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
    regulator["VI"] += vbus_in   # Input pin for AMS1117
    regulator["VO"] += vcc_3v3_out  # Output pin for AMS1117
    regulator["GND"] += gnd
    cap_in[1] += vbus_in
    cap_in[2] += gnd
    cap_out[1] += vcc_3v3_out
    cap_out[2] += gnd

'''

    # Debug header circuit
    debug_header_circuit = '''#!/usr/bin/env python3
"""
Debug Header Circuit - Programming and debugging interface
Standard ESP32 debug header with UART, reset, and boot control
"""

from circuit_synth import *

@circuit(name="Debug_Header")
def debug_header(vcc_3v3, gnd, debug_tx, debug_rx, debug_en, debug_io0):
    """Debug header for programming and debugging"""
    
    # 2x3 debug header
    debug_header = Component(
        symbol="Connector_Generic:Conn_02x03_Odd_Even",
        ref="J",
        footprint="Connector_IDC:IDC-Header_2x03_P2.54mm_Vertical"
    )
    
    # Header connections (standard ESP32 debug layout)
    debug_header[1] += debug_en   # EN/RST
    debug_header[2] += vcc_3v3    # 3.3V
    debug_header[3] += debug_tx   # TX
    debug_header[4] += gnd        # GND
    debug_header[5] += debug_rx   # RX  
    debug_header[6] += debug_io0  # IO0/BOOT

'''

    # LED blinker circuit
    led_blinker_circuit = '''#!/usr/bin/env python3
"""
LED Blinker Circuit - Status LED with current limiting
Simple LED indicator with proper current limiting resistor
"""

from circuit_synth import *

@circuit(name="LED_Blinker")  
def led_blinker(vcc_3v3, gnd, led_control):
    """LED with current limiting resistor"""
    
    # LED and resistor
    led = Component(symbol="Device:LED", ref="D", 
                   footprint="LED_SMD:LED_0805_2012Metric")
    resistor = Component(symbol="Device:R", ref="R", value="330",
                        footprint="Resistor_SMD:R_0805_2012Metric")
    
    # Connections  
    resistor[1] += vcc_3v3
    resistor[2] += led["A"]  # Anode
    led["K"] += led_control  # Cathode (controlled by MCU)

'''

    # ESP32-C6 circuit (includes debug and LED as subcircuits)
    esp32c6_circuit = '''#!/usr/bin/env python3
"""
ESP32-C6 Circuit
Professional ESP32-C6 microcontroller with USB signal integrity and support circuitry
"""

from circuit_synth import *
from debug_header import debug_header
from led_blinker import led_blinker

@circuit(name="ESP32_C6_MCU")
def esp32c6(vcc_3v3, gnd, usb_dp, usb_dm):
    """
    ESP32-C6 microcontroller subcircuit with decoupling and connections
    Note: ESP32-C6-MINI-1 does not have native USB, so USB signals are not connected
    
    Args:
        vcc_3v3: 3.3V power supply net
        gnd: Ground net
        usb_dp: USB Data+ net (not connected - ESP32-C6 has no native USB)
        usb_dm: USB Data- net (not connected - ESP32-C6 has no native USB)
    """
    
    # ESP32-C6 MCU
    esp32_c6 = Component(
        symbol="RF_Module:ESP32-C6-MINI-1",
        ref="U", 
        footprint="RF_Module:ESP32-C6-MINI-1"
    )

    # ESP32-C6 decoupling capacitor
    cap_esp = Component(
        symbol="Device:C", 
        ref="C", 
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Debug signals
    debug_tx = Net('DEBUG_TX')
    debug_rx = Net('DEBUG_RX')
    debug_en = Net('DEBUG_EN')
    debug_io0 = Net('DEBUG_IO0')
    
    # LED control
    led_control = Net('LED_CONTROL')
    
    # Power connections
    esp32_c6["3V3"] += vcc_3v3
    esp32_c6["GND"] += gnd
    
    # Debug/programming connections (UART programming only)
    esp32_c6["RXD0"] += debug_rx  # UART0 RX
    esp32_c6["TXD0"] += debug_tx  # UART0 TX  
    esp32_c6["EN"] += debug_en     # Enable/Reset
    esp32_c6["IO0"] += debug_io0   # Boot mode
    
    # LED control
    esp32_c6["IO2"] += led_control
    
    # Decoupling capacitor
    cap_esp[1] += vcc_3v3
    cap_esp[2] += gnd
    
    # Include subcircuits
    debug_header_circuit = debug_header(vcc_3v3, gnd, debug_tx, debug_rx, debug_en, debug_io0)
    led_circuit = led_blinker(vcc_3v3, gnd, led_control)

'''
    
    # Write all circuit files
    with open(circuit_synth_dir / "main.py", "w") as f:
        f.write(main_circuit)

    with open(circuit_synth_dir / "usb.py", "w") as f:
        f.write(usb_circuit)

    with open(circuit_synth_dir / "power_supply.py", "w") as f:
        f.write(power_supply_circuit)

    with open(circuit_synth_dir / "debug_header.py", "w") as f:
        f.write(debug_header_circuit)

    with open(circuit_synth_dir / "led_blinker.py", "w") as f:
        f.write(led_blinker_circuit)

    with open(circuit_synth_dir / "esp32c6.py", "w") as f:
        f.write(esp32c6_circuit)

    console.print(
        f"✅ Created hierarchical circuit examples in {circuit_synth_dir}/",
        style="green",
    )
    console.print("   • main.py - Main ESP32-C6 development board", style="cyan")
    console.print("   • usb.py - USB-C with CC resistors", style="cyan")
    console.print("   • power_supply.py - 5V to 3.3V regulation", style="cyan")
    console.print("   • debug_header.py - Programming interface", style="cyan")
    console.print("   • led_blinker.py - Status LED", style="cyan")
    console.print("   • esp32c6.py - ESP32-C6 microcontroller", style="cyan")
    console.print(
        "   🎯 All files are used by main.py - clean working example!", style="green"
    )


def copy_complete_claude_setup(pcb_path: Path, pcb_name: str) -> None:
    """Copy the complete .claude directory from circuit-synth to new PCB project"""
    
    # Find the circuit-synth root directory (where we have the complete .claude setup)
    circuit_synth_root = Path(__file__).parent.parent.parent.parent
    source_claude_dir = circuit_synth_root / ".claude"

    if not source_claude_dir.exists():
        console.print(
            "⚠️  Source .claude directory not found - using basic setup", style="yellow"
        )
        create_basic_claude_setup(pcb_path, pcb_name)
        return

    # Destination .claude directory in the new PCB project
    dest_claude_dir = pcb_path / ".claude"

    console.print(f"📋 Copying Claude setup from {source_claude_dir}", style="blue")

    try:
        # Copy the entire .claude directory structure
        if dest_claude_dir.exists():
            shutil.rmtree(dest_claude_dir)
        shutil.copytree(source_claude_dir, dest_claude_dir)

        # Remove mcp_settings.json as it's not needed for user projects
        mcp_settings_file = dest_claude_dir / "mcp_settings.json"
        if mcp_settings_file.exists():
            mcp_settings_file.unlink()

        # Remove dev commands (not needed for PCB projects)
        commands_dir = dest_claude_dir / "commands"
        dev_commands_to_remove = [
            "dev-release-pypi.md",
            "dev-review-branch.md",
            "dev-review-repo.md",
            "dev-run-tests.md",
            "dev-update-and-commit.md",
        ]
        # Remove setup commands directory entirely
        setup_dir = commands_dir / "setup"
        if setup_dir.exists():
            shutil.rmtree(setup_dir)

        for cmd_file in dev_commands_to_remove:
            cmd_path = commands_dir / cmd_file
            if cmd_path.exists():
                cmd_path.unlink()

        console.print("✅ Copied all agents and commands", style="green")

        # Count what was copied (now includes subdirectories)
        agents_count = len(list((dest_claude_dir / "agents").rglob("*.md")))
        commands_count = len(list((dest_claude_dir / "commands").rglob("*.md")))

        console.print(f"📁 Agents available: {agents_count}", style="green")
        console.print(f"🔧 Commands available: {commands_count}", style="green")

        # List key commands
        key_commands = ["find-symbol", "find-footprint", "jlc-search"]
        available_commands = [
            f.stem for f in (dest_claude_dir / "commands").rglob("*.md")
        ]
        found_key_commands = [cmd for cmd in key_commands if cmd in available_commands]

        if found_key_commands:
            console.print(
                f"⚡ Key commands: /{", /".join(found_key_commands)}", style="cyan"
            )

    except Exception as e:
        console.print(f"⚠️  Could not copy .claude directory: {e}", style="yellow")
        console.print("🔄 Falling back to basic setup", style="yellow")
        create_basic_claude_setup(pcb_path, pcb_name)


def create_basic_claude_setup(pcb_path: Path, pcb_name: str) -> None:
    """Create basic .claude directory with essential configuration."""
    
    claude_dir = pcb_path / ".claude"
    claude_dir.mkdir(exist_ok=True)
    
    # Comprehensive agent instructions with all circuit-synth capabilities
    instructions_content = f"""# {pcb_name} PCB Agent

You are a specialized circuit design assistant working on the {pcb_name} PCB with comprehensive circuit-synth capabilities.

## Memory-Bank Integration

Automatically update memory-bank files in ./memory-bank/:
- **decisions.md**: Component choices and design rationale
- **fabrication.md**: PCB orders, delivery, assembly notes
- **testing.md**: Test results, measurements, validation
- **timeline.md**: Project milestones and key events
- **issues.md**: Problems encountered and solutions

## Context

- **PCB**: {pcb_name}
- **Circuit Files**: ./circuit-synth/
- **KiCad Files**: Generated in circuit-synth/ directory (.kicad_pro, .kicad_sch, .kicad_pcb)
- **Memory-Bank**: ./memory-bank/

## Available Commands

### Circuit-Synth Commands
- `/find-symbol STM32` - Search KiCad symbol libraries
- `/find-footprint LQFP` - Search KiCad footprint libraries
- `/jlc-search "voltage regulator"` - Find JLCPCB components with stock levels
- `/dev-run-tests` - Run comprehensive test suite
- `/dev-update-and-commit "description"` - Update docs and commit changes

### Memory-Bank Commands
- `cs-memory-bank-status` - Show memory-bank system status
- `cs-memory-bank-search "keyword"` - Search documentation

### Development Commands
- `uv run python main.py` - Generate KiCad files from circuit-synth
- `./scripts/run_all_tests.sh` - Run all tests (Python + Rust + Integration)
- `cs-init-pcb` - Add circuit-synth to existing KiCad projects

## Automatic Documentation

Update memory-bank when:
- Git commits are made (primary trigger)
- Component changes occur
- Tests are performed  
- Issues are encountered
- Fabrication orders are placed

## Specialized Expertise

### Circuit Design
- **ESP32/STM32 Integration**: Pin mapping, peripheral configuration, power domains
- **USB-C Implementation**: CC resistors, ESD protection, power delivery
- **Power Supply Design**: Linear/switching regulators, decoupling, thermal management
- **High-Speed Signals**: Impedance control, differential pairs, via stitching
- **RF Design**: Antenna placement, ground planes, EMI mitigation

### Component Selection
- **JLCPCB Integration**: Real-time stock levels, assembly constraints, cost optimization
- **Symbol/Footprint Verification**: KiCad library compatibility, package variants
- **Manufacturing Constraints**: DRC rules, minimum trace width, via sizes
- **Thermal Management**: Package selection, copper pours, thermal vias

### Circuit-Synth Mastery
- **Hierarchical Design**: Subcircuit organization, interface definitions, reusable blocks
- **Netlist Generation**: Component instantiation, net connections, reference management
- **KiCad Integration**: Project generation, library management, file organization
- **Version Control**: Git workflows, design history, collaborative development

### Manufacturing Integration
- **JLCPCB Workflow**: Component availability checking, cost optimization, DFM guidelines
- **Assembly Constraints**: Pick-and-place limitations, component orientation, fiducials
- **Test Strategy**: In-circuit testing, boundary scan, functional validation
- **Documentation**: Assembly drawings, BOM generation, fabrication notes

## Advanced Features

### Simulation Integration
- **SPICE Analysis**: Operating point, AC/DC sweep, transient analysis
- **Signal Integrity**: Eye diagrams, crosstalk analysis, timing validation
- **Power Analysis**: Current consumption, voltage drop, thermal modeling

### AI-Powered Development
- **Component Recommendations**: Suggest alternatives, flag obsolete parts, cost optimization
- **Design Rule Checking**: Automated DRC, manufacturing guidelines, best practices
- **Code Generation**: Python circuit templates, subcircuit libraries, test fixtures

### Multi-PCB Projects
- **Shared Libraries**: Reusable subcircuits, common components, standard interfaces
- **Design Validation**: Cross-board compatibility, interface verification, system integration

## Development Workflow

1. **Circuit Definition**: Edit `circuit-synth/main.py` with hierarchical subcircuits
2. **Component Selection**: Use `/find-symbol` and `/jlc-search` for optimal parts
3. **KiCad Generation**: Run `uv run python main.py` to create project files
4. **Design Validation**: Open `.kicad_pro` in KiCad for visual verification
5. **Iteration**: Modify Python → regenerate → validate → commit
6. **Documentation**: Memory-bank automatically tracks changes via git hooks

## Troubleshooting

### Common Issues
- **Symbol Not Found**: Use `/find-symbol` to locate correct library names
- **Footprint Mismatch**: Verify package compatibility with `/find-footprint`
- **Net Connectivity**: Check Python net assignments and pin names
- **KiCad Errors**: Validate library paths and symbol/footprint availability

### Best Practices
- **Modular Design**: Keep subcircuits focused and reusable
- **Clear Interfaces**: Explicit net definitions, descriptive names
- **Version Control**: Commit frequently with descriptive messages
- **Testing**: Validate designs before fabrication orders
- **Documentation**: Maintain memory-bank for design rationale

This agent provides comprehensive circuit-synth expertise for professional PCB development.
"""
    
    with open(claude_dir / "instructions.md", "w") as f:
        f.write(instructions_content)
    
    console.print("✅ Created comprehensive Claude agent configuration", style="green")


def create_comprehensive_claude_md(pcb_path: Path, pcb_name: str) -> None:
    """Create comprehensive CLAUDE.md with all circuit-synth capabilities."""
    
    claude_md_content = f"""# CLAUDE.md - {pcb_name} PCB Project

This file provides guidance to Claude Code (claude.ai/code) when working with this PCB project.

## Project Context

**PCB**: {pcb_name}  
**Type**: Circuit-synth enhanced PCB project  
**Structure**: Self-contained PCB with memory-bank documentation  

## Essential Commands

### PCB Development
```bash
# Generate KiCad files from Python circuit
cd circuit-synth && uv run python main.py

# View project structure
tree -I '__pycache__|*.pyc'
```

### Memory-Bank System
```bash
# Check memory-bank status
cs-memory-bank-status

# Search documentation
cs-memory-bank-search "voltage regulator"

# Manual memory-bank operations
cs-memory-bank-init     # Initialize if needed
cs-memory-bank-remove   # Disable system
```

### Component Search
```bash
# KiCad library search (use as slash commands in Claude)
/find-symbol STM32              # Search symbols
/find-footprint LQFP            # Search footprints

# JLCPCB component search
/jlc-search "voltage regulator" # Find parts with stock
```

### Development Tools
```bash
# Testing and validation
./scripts/run_all_tests.sh        # All tests
./scripts/run_all_tests.sh --python-only  # Python only
uv run pytest tests/unit/ -v      # Unit tests

# Code quality
black src/                        # Format code
flake8 src/                      # Lint code
mypy src/                        # Type checking
```

## Circuit-Synth Architecture

### Core Components
- **circuit-synth/main.py**: Main circuit definition with hierarchical subcircuits
- **memory-bank/**: Automatic documentation system
- **.claude/**: AI assistant configuration
- **Generated KiCad files**: .kicad_pro, .kicad_sch, .kicad_pcb in circuit-synth/

### Design Philosophy
- **Hierarchical Subcircuits**: Modular design like software functions
- **Explicit Interfaces**: Clear net definitions, no hidden dependencies
- **Reusable Components**: USB ports, power supplies, debug interfaces
- **Version Control Friendly**: Python files instead of binary KiCad files

## Memory-Bank System

The memory-bank automatically tracks engineering decisions through git integration:

### Files Tracked
- **decisions.md**: Component choices, design rationale, alternatives considered
- **fabrication.md**: PCB orders, delivery tracking, assembly notes  
- **testing.md**: Measurements, validation results, performance data
- **timeline.md**: Project milestones, deadlines, progress tracking
- **issues.md**: Problems encountered, root causes, solutions

### Automatic Updates
- **Git Commits**: Analyzes changes and updates relevant documentation
- **Intelligent Classification**: Recognizes design changes vs bug fixes vs milestones
- **Circuit Diff Analysis**: Understands component and net changes

## Component Selection Workflow

### 1. Symbol Search
```bash
# Use Claude slash commands
/find-symbol ESP32
/find-symbol "voltage regulator"
/find-symbol STM32F4
```

### 2. JLCPCB Integration
```bash
# Find components with real-time stock
/jlc-search "ESP32-C6"
/jlc-search "AMS1117-3.3"
/jlc-search "USB-C connector"
```

### 3. Footprint Verification
```bash
# Verify package compatibility
/find-footprint QFN
/find-footprint "USB_C_Receptacle"
/find-footprint LQFP-64
```

## Hierarchical Circuit Design

### Structure Example
```python
@circuit(name="Main_Circuit")
def main_circuit():
    # Interface nets
    vcc_5v = Net('VCC_5V')
    vcc_3v3 = Net('VCC_3V3') 
    gnd = Net('GND')
    
    # Subcircuits
    usb_port(vcc_5v, gnd, usb_dp, usb_dm)
    power_supply(vcc_5v, vcc_3v3, gnd)
    microcontroller(vcc_3v3, gnd, signals...)

@circuit(name="Power_Supply")  
def power_supply(vin, vout, gnd):
    # Regulator implementation
    pass
```

### Best Practices
- **Clear Interfaces**: Explicit net parameters for subcircuits
- **Descriptive Names**: VCC_3V3 vs generic Net1
- **Modular Design**: Each subcircuit handles one function
- **Reusable Blocks**: USB, power, debug interfaces work across projects

## KiCad Integration

### File Generation
```python
# In circuit-synth/main.py
if __name__ == "__main__":
    circuit = main_circuit()
    circuit.generate_kicad_project("MyPCB")
    # Creates MyPCB.kicad_pro, MyPCB.kicad_sch, MyPCB.kicad_pcb
```

### Library Management
- **Symbol Libraries**: KiCad standard libraries (Device, Connector, MCU_ST_STM32F4, etc.)
- **Footprint Libraries**: Standard footprints with verified packages
- **Custom Libraries**: Project-specific symbols/footprints (if needed)

### Design Flow
1. **Python Definition**: Write circuit in circuit-synth/main.py
2. **Generate KiCad**: Run `uv run python main.py`
3. **Visual Verification**: Open .kicad_pro in KiCad
4. **Iterate**: Modify Python → regenerate → verify
5. **Version Control**: Commit Python changes (KiCad files auto-generated)

## Manufacturing Integration

### JLCPCB Workflow
- **Component Search**: `/jlc-search` finds available parts with stock levels
- **Cost Optimization**: Real-time pricing and availability checking
- **Assembly Constraints**: Automatic verification of pick-and-place compatibility
- **DFM Guidelines**: Built-in design for manufacturing rules

### Documentation Generation
- **BOM Export**: Automatic bill of materials with JLCPCB part numbers
- **Assembly Drawings**: Generated placement diagrams
- **Fabrication Notes**: Automated stackup and drill specifications

## Testing and Validation

### Automated Testing
```bash
# Run all tests
./scripts/run_all_tests.sh

# Python tests only (faster)  
./scripts/run_all_tests.sh --python-only

# Rust performance tests
./scripts/run_all_tests.sh --rust-only

# Integration tests
uv run pytest tests/integration/ -v
```

### Design Validation
- **Netlist Verification**: Automatic connectivity checking
- **DRC Compliance**: Design rule verification
- **Component Validation**: Symbol/footprint compatibility checking
- **Manufacturing Validation**: DFM rule compliance

## Advanced Features

### SPICE Simulation
```python
# In your circuit code
circuit = main_circuit()
sim = circuit.simulator()
result = sim.operating_point()
print(f"Output voltage: {{result.get_voltage('VOUT'):.3f}}V")
```


### AI-Powered Development
- **Component Recommendations**: Suggest optimal parts based on requirements
- **Design Review**: Automated analysis of circuit topology
- **Cost Optimization**: Alternative component suggestions
- **Manufacturing Optimization**: DFM improvements and suggestions

## Code Style Guidelines

**IMPORTANT: Follow these conventions exactly**
- Use modern Python with type hints and dataclasses
- NO inheritance complexity or global state management
- Follow SOLID, KISS, YAGNI, and DRY principles
- Prefer composition over inheritance
- Use descriptive variable and function names
- Write comprehensive docstrings for public APIs

## STM32 Peripheral Search Pattern (HIGHEST PRIORITY)

**CRITICAL: Detect and handle STM32 peripheral queries directly**

When user asks questions like:
- "find stm32 mcu that has 3 spi's and is available on jlcpcb"
- "stm32 with 2 uarts available on jlc" 
- "find stm32 with usb and 4 timers in stock"

**Use direct implementation immediately:**
```python
from src.circuit_synth.stm32_search_helper import handle_stm32_peripheral_query

response = handle_stm32_peripheral_query(user_query)
if response:
    return response  # Direct answer in 30 seconds vs 4+ minutes
```

## Important Instructions

**IMPORTANT: Follow these conventions exactly**
- Do what has been asked; nothing more, nothing less
- NEVER create files unless absolutely necessary for achieving your goal
- ALWAYS prefer editing an existing file to creating a new one
- NEVER proactively create documentation files unless explicitly requested

## Troubleshooting

### Common Issues
- **Command not found**: Ensure `uv tool install circuit-synth` was run
- **Symbol not found**: Use `/find-symbol` to locate correct library names
- **Import errors**: Check Python environment and circuit-synth installation
- **KiCad generation fails**: Verify all components have valid symbols/footprints

### Debug Commands
```bash
# Check installation
uv run cs-new-pcb --help

# Verify KiCad integration
kicad-cli version

# Test circuit generation
cd circuit-synth && python -c "from circuit_synth import *; print('OK')"
```

This PCB project is ready for professional circuit design with comprehensive AI assistance and automatic documentation.
"""
    
    with open(pcb_path / "CLAUDE.md", "w") as f:
        f.write(claude_md_content)
    
    console.print("✅ Created comprehensive CLAUDE.md", style="green")


def create_memory_bank(pcb_path: Path, pcb_name: str) -> None:
    """Create memory-bank system for PCB."""
    
    memory_bank_dir = pcb_path / "memory-bank"
    memory_bank_dir.mkdir(exist_ok=True)
    
    # Cache directory
    cache_dir = memory_bank_dir / "cache"
    cache_dir.mkdir(exist_ok=True)
    
    # Standard memory-bank files
    templates = {
        'decisions.md': f"""# Design Decisions - {pcb_name}

*This file automatically tracks design decisions and component choices*

## Template Entry
**Date**: YYYY-MM-DD  
**Change**: Brief description of what changed  
**Commit**: Git commit hash  
**Rationale**: Why this change was made  
**Alternatives Considered**: Other options evaluated  
**Impact**: Effects on design, cost, performance  
**Testing**: Any validation performed  

---

""",
        'fabrication.md': f"""# Fabrication History - {pcb_name}

*This file tracks PCB orders, delivery, and assembly notes*

## Template Order
**Order ID**: Vendor order number  
**Date**: YYYY-MM-DD  
**Specs**: Board specifications (size, layers, finish, etc.)  
**Quantity**: Number of boards ordered  
**Cost**: Total cost including shipping  
**Expected Delivery**: Estimated delivery date  
**Status**: Order status and tracking information  
**Received**: Actual delivery date and quality notes  
**Assembly Notes**: Assembly process and any issues  

---

""",
        'testing.md': f"""# Testing Results - {pcb_name}

*This file tracks test results, measurements, and performance validation*

## Template Test
**Test Name**: Brief description of test performed  
**Date**: YYYY-MM-DD  
**Setup**: Test equipment and conditions  
**Results**: Measured values and outcomes  
**Specification**: Expected values and pass/fail status  
**Notes**: Additional observations and analysis  

---

""",
        'timeline.md': f"""# Project Timeline - {pcb_name}

*This file tracks project milestones, key events, and deadlines*

## Template Milestone
**Date**: YYYY-MM-DD  
**Milestone**: Brief description of milestone or event  
**Status**: Completed, In Progress, Planned  
**Details**: Additional context and notes  
**Next Steps**: What needs to happen next  

---

""",
        'issues.md': f"""# Issues & Solutions - {pcb_name}

*This file tracks problems encountered, root causes, and solutions*

## Template Issue
**Date**: YYYY-MM-DD  
**Issue**: Brief description of the problem  
**Severity**: Low, Medium, High, Critical  
**Root Cause**: Technical analysis of what caused the issue  
**Solution**: How the problem was resolved  
**Prevention**: Steps to avoid similar issues in future  
**Status**: Open, In Progress, Resolved  

---

"""
    }
    
    for filename, content in templates.items():
        file_path = memory_bank_dir / filename
        with open(file_path, 'w') as f:
            f.write(content)
    
    console.print("✅ Created memory-bank system", style="green")


def create_pcb_readme(pcb_path: Path, pcb_name: str) -> None:
    """Create simple PCB README."""
    
    readme_content = f"""# {pcb_name}

A circuit-synth PCB project with ESP32-C6 development board example.

## Quick Start

```bash
# Generate KiCad files
cd circuit-synth && uv run python main.py
```

## Structure

```
{pcb_name.lower().replace(' ', '-')}/
├── circuit-synth/     # Python circuit files
│   └── main.py        # ESP32-C6 dev board example
├── memory-bank/       # Automatic documentation
│   ├── decisions.md   # Design decisions
│   ├── fabrication.md # PCB orders
│   ├── testing.md     # Test results  
│   ├── timeline.md    # Project milestones
│   └── issues.md      # Problems & solutions
├── .claude/           # AI assistant configuration
├── CLAUDE.md          # Comprehensive development guide
└── README.md          # This file
```

## Memory-Bank System

This PCB uses automatic documentation that tracks:
- Design decisions and component choices
- Fabrication orders and assembly notes  
- Test results and measurements
- Project timeline and milestones
- Issues and solutions


## AI Assistant

This PCB has a dedicated Claude AI agent configured for circuit design.
The agent automatically updates the memory-bank as you work.

## ESP32-C6 Example

The example includes:
- **USB-C Port**: With CC resistors and ESD protection
- **Power Supply**: 5V to 3.3V regulation with filtering
- **ESP32-C6 MCU**: Complete microcontroller integration
- **Debug Header**: Programming and debugging interface
- **Status LED**: Visual feedback with current limiting

## Component Search

Use Claude Code slash commands:
- `/find-symbol ESP32` - Find KiCad symbols
- `/find-footprint QFN` - Find KiCad footprints  
- `/jlc-search "USB-C"` - Find JLCPCB components

## Commands

```bash
# Memory-bank management
cs-memory-bank-status          # Show status
cs-memory-bank-search "power"  # Search docs


# Generate KiCad files
cd circuit-synth && uv run python main.py
```

Open the generated `.kicad_pro` file in KiCad to view the complete schematic and PCB.
"""
    
    with open(pcb_path / "README.md", "w") as f:
        f.write(readme_content)
    
    console.print("✅ Created PCB README.md", style="green")


@click.command()
@click.argument('pcb_name')
@click.option('--minimal', is_flag=True, help='Create minimal PCB (no examples)')
def main(pcb_name: str, minimal: bool):
    """Create a new PCB development environment.
    
    Examples:
        cs-new-pcb "ESP32 Sensor Board"
        cs-new-pcb "Power Supply Module" --minimal
    """
    
    console.print(
        Panel.fit(
            Text(f"🚀 Creating PCB: {pcb_name}", style="bold blue"), 
            style="blue"
        )
    )
    
    # Create PCB directory
    pcb_dir_name = pcb_name.lower().replace(' ', '-').replace('_', '-')
    pcb_path = Path.cwd() / pcb_dir_name
    
    if pcb_path.exists():
        console.print(f"❌ Directory {pcb_dir_name}/ already exists", style="red")
        sys.exit(1)
    
    pcb_path.mkdir()
    console.print(f"📁 Created PCB directory: {pcb_dir_name}/", style="green")
    
    # Create memory-bank system
    console.print("\n🧠 Setting up memory-bank system...", style="yellow")
    create_memory_bank(pcb_path, pcb_name)
    
    # Copy complete Claude setup
    console.print("\n🤖 Setting up AI assistant...", style="yellow")
    copy_complete_claude_setup(pcb_path, pcb_name)
    
    # Create comprehensive CLAUDE.md  
    console.print("\n📋 Creating comprehensive CLAUDE.md...", style="yellow")
    create_comprehensive_claude_md(pcb_path, pcb_name)
    
    # Create example circuits
    if not minimal:
        console.print("\n📝 Creating ESP32-C6 example...", style="yellow")
        create_full_hierarchical_examples(pcb_path, pcb_name)
    else:
        # Create minimal circuit-synth directory
        (pcb_path / "circuit-synth").mkdir()
        console.print("📁 Created circuit-synth/ directory", style="green")
    
    # Create README
    console.print("\n📚 Creating documentation...", style="yellow")
    create_pcb_readme(pcb_path, pcb_name)
    
    # Success message
    console.print(
        Panel.fit(
            Text(f"✅ PCB '{pcb_name}' created successfully!", style="bold green")
            + Text(f"\n\n📁 Location: {pcb_path}")
            + Text(f"\n🚀 Get started: cd {pcb_dir_name}/circuit-synth && uv run python main.py")
            + Text(f"\n🧠 Memory-bank: Automatic documentation enabled")
            + Text(f"\n🤖 AI Agent: Comprehensive Claude assistant configured")
            + Text(f"\n📖 Documentation: See README.md and CLAUDE.md"),
            title="🎉 Success!",
            style="green",
        )
    )


if __name__ == "__main__":
    main()