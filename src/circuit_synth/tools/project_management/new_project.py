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
from rich.prompt import Confirm
from rich.text import Text

# Import circuit-synth modules
from circuit_synth.ai_integration.claude.agent_registry import register_circuit_agents
from circuit_synth.core.kicad_validator import validate_kicad_installation

# Import new interactive CLI modules
from .interactive_cli import run_interactive_setup, parse_cli_flags
from .template_manager import TemplateManager, READMEGenerator, CLAUDEMDGenerator
from .project_config import get_default_config

console = Console()


def create_claude_directory_from_templates(
    project_path: Path, developer_mode: bool = False
) -> None:
    """Create a complete .claude directory structure using templates and agent registry

    Args:
        project_path: Target project directory
        developer_mode: If True, includes contributor agents and dev commands
    """
    dest_claude_dir = project_path / ".claude"
    dest_claude_dir.mkdir(exist_ok=True)

    console.print(
        "🤖 Setting up Claude Code integration from templates...", style="blue"
    )

    try:
        # Find the template directory
        circuit_synth_dir = Path(
            __file__
        ).parent.parent.parent  # Get to circuit_synth directory
        template_claude_dir = (
            circuit_synth_dir / "data" / "templates" / "example_project" / ".claude"
        )

        if template_claude_dir.exists():
            console.print(
                f"📋 Copying templates from {template_claude_dir}", style="blue"
            )

            # Copy the entire template .claude directory structure
            if dest_claude_dir.exists():
                shutil.rmtree(dest_claude_dir)
            shutil.copytree(template_claude_dir, dest_claude_dir)

            # Handle developer mode filtering
            commands_dir = dest_claude_dir / "commands"
            agents_dir = dest_claude_dir / "agents"

            if not developer_mode:
                # Remove dev commands (not needed for end users)
                dev_commands_to_remove = [
                    "development/dev-release-pypi.md",
                    "development/dev-review-branch.md",
                    "development/dev-review-repo.md",
                    "development/dev-run-tests.md",
                    "development/dev-update-and-commit.md",
                ]
                # Remove setup commands directory entirely for end users
                setup_dir = commands_dir / "setup"
                if setup_dir.exists():
                    shutil.rmtree(setup_dir)

                # Remove development commands directory for end users
                dev_commands_dir = commands_dir / "development"
                if dev_commands_dir.exists():
                    shutil.rmtree(dev_commands_dir)

                for cmd_file in dev_commands_to_remove:
                    cmd_path = commands_dir / cmd_file
                    if cmd_path.exists():
                        cmd_path.unlink()

                # Remove development agents (not needed for end users)
                dev_agents_to_remove = [
                    "development/contributor.md",
                    "development/first_setup_agent.md",
                    "development/circuit_generation_agent.md",
                ]
                for agent_file in dev_agents_to_remove:
                    agent_path = agents_dir / agent_file
                    if agent_path.exists():
                        agent_path.unlink()

                # Remove development agents directory if empty
                dev_agents_dir = agents_dir / "development"
                if dev_agents_dir.exists() and not any(dev_agents_dir.iterdir()):
                    dev_agents_dir.rmdir()

            console.print("✅ Copied complete template structure", style="green")

        else:
            console.print(
                "⚠️  Template directory not found, using basic setup", style="yellow"
            )
            # Fallback: just register agents
            register_circuit_agents()

        # Also register agents to update with any newer agent definitions
        register_circuit_agents()

        # Hooks removed - they caused more problems than they solved
        console.print("✅ Clean environment setup (no hooks)", style="green")

        # Remove mcp_settings.json as it's not needed for user projects
        mcp_settings_file = dest_claude_dir / "mcp_settings.json"
        if mcp_settings_file.exists():
            mcp_settings_file.unlink()

        # Count what was created
        agents_count = len(list((dest_claude_dir / "agents").rglob("*.md")))
        commands_count = len(list((dest_claude_dir / "commands").rglob("*.md")))

        console.print(f"📁 Agents available: {agents_count}", style="green")
        console.print(f"🔧 Commands available: {commands_count}", style="green")

        console.print(
            "✅ Created Claude directory structure with templates", style="green"
        )
        console.print(
            f"📁 Created project-local .claude in {dest_claude_dir}", style="blue"
        )

    except Exception as e:
        console.print(
            f"⚠️  Could not create complete Claude setup: {str(e)}", style="yellow"
        )
        # Fall back to basic agent registration
        register_circuit_agents()


def copy_complete_claude_setup(
    project_path: Path, developer_mode: bool = False
) -> None:
    """Copy the complete .claude directory from circuit-synth to new project

    Args:
        project_path: Target project directory
        developer_mode: If True, includes contributor agents and dev commands
    """

    # Find the circuit-synth root directory (where we have the complete .claude setup)
    circuit_synth_root = Path(__file__).parent.parent.parent.parent
    source_claude_dir = circuit_synth_root / ".claude"

    if not source_claude_dir.exists():
        console.print(
            "⚠️  Source .claude directory not found - using template-based setup",
            style="yellow",
        )
        # Use template-based approach to create complete .claude directory
        create_claude_directory_from_templates(project_path, developer_mode)
        return

    # Destination .claude directory in the new project
    dest_claude_dir = project_path / ".claude"

    console.print(f"📋 Copying Claude setup from {source_claude_dir}", style="blue")
    if developer_mode:
        console.print(
            "🔧 Developer mode: Including contributor agents and dev tools",
            style="cyan",
        )

    try:
        # Copy the entire .claude directory structure
        if dest_claude_dir.exists():
            shutil.rmtree(dest_claude_dir)
        shutil.copytree(source_claude_dir, dest_claude_dir)

        # Remove mcp_settings.json as it's not needed for user projects
        mcp_settings_file = dest_claude_dir / "mcp_settings.json"
        if mcp_settings_file.exists():
            mcp_settings_file.unlink()

        # Handle commands and agents based on mode
        commands_dir = dest_claude_dir / "commands"
        agents_dir = dest_claude_dir / "agents"

        if not developer_mode:
            # Remove dev commands (not needed for end users)
            dev_commands_to_remove = [
                "dev-release-pypi.md",
                "dev-review-branch.md",
                "dev-review-repo.md",
                "dev-run-tests.md",
                "dev-update-and-commit.md",
            ]
            # Remove setup commands directory entirely for end users
            setup_dir = commands_dir / "setup"
            if setup_dir.exists():
                shutil.rmtree(setup_dir)

            for cmd_file in dev_commands_to_remove:
                cmd_path = commands_dir / cmd_file
                if cmd_path.exists():
                    cmd_path.unlink()

            # Remove development agents (not needed for end users)
            dev_agents_to_remove = [
                "development/contributor.md",
                "development/first_setup_agent.md",
                "development/circuit_generation_agent.md",
            ]
            for agent_file in dev_agents_to_remove:
                agent_path = agents_dir / agent_file
                if agent_path.exists():
                    agent_path.unlink()

        else:
            console.print("✅ Keeping all developer tools and agents", style="green")

        console.print("✅ Copied all agents and commands", style="green")

        # Hooks removed - they caused more problems than they solved
        console.print("✅ Clean environment setup (no hooks)", style="green")

        # Count what was copied (now includes subdirectories)
        agents_count = len(list((dest_claude_dir / "agents").rglob("*.md")))
        commands_count = len(list((dest_claude_dir / "commands").rglob("*.md")))

        console.print(f"📁 Agents available: {agents_count}", style="green")
        console.print(f"🔧 Commands available: {commands_count}", style="green")

        # List key agents by category
        circuit_agents = []
        manufacturing_agents = []
        development_agents = []
        quality_agents = []

        for agent_file in (dest_claude_dir / "agents").rglob("*.md"):
            agent_name = agent_file.stem
            if "circuit" in agent_file.parent.name:
                circuit_agents.append(agent_name)
            elif "manufacturing" in agent_file.parent.name:
                manufacturing_agents.append(agent_name)
            elif "development" in agent_file.parent.name:
                development_agents.append(agent_name)
            elif "quality" in agent_file.parent.name:
                quality_agents.append(agent_name)

        if circuit_agents:
            console.print(
                f"🔌 Circuit agents: {', '.join(circuit_agents)}", style="cyan"
            )
        if manufacturing_agents:
            console.print(
                f"🏭 Manufacturing agents: {', '.join(manufacturing_agents)}",
                style="cyan",
            )
        if quality_agents:
            console.print(
                f"✅ Quality agents: {', '.join(quality_agents)}", style="cyan"
            )
        if development_agents and developer_mode:
            console.print(
                f"🔧 Development agents: {', '.join(development_agents)}", style="cyan"
            )

        # List some key commands
        key_commands = ["find-symbol", "find-footprint", "jlc-search"]
        if developer_mode:
            key_commands.extend(["dev-run-tests", "dev-review-branch"])

        available_commands = [
            f.stem for f in (dest_claude_dir / "commands").rglob("*.md")
        ]
        found_key_commands = [cmd for cmd in key_commands if cmd in available_commands]

        if found_key_commands:
            console.print(
                f"⚡ Key commands: /{', /'.join(found_key_commands)}", style="cyan"
            )

    except Exception as e:
        console.print(f"⚠️  Could not copy .claude directory: {e}", style="yellow")
        console.print("🔄 Falling back to basic agent registration", style="yellow")
        register_circuit_agents()


def check_kicad_installation() -> Dict[str, Any]:
    """Check KiCad installation and return path info (cross-platform)"""
    console.print("🔍 Checking KiCad installation...", style="yellow")

    try:
        result = validate_kicad_installation()

        # Check if KiCad CLI is available (main requirement)
        if result.get("cli_available", False):
            console.print("✅ KiCad found!", style="green")
            console.print(f"   🔧 CLI Path: {result.get('cli_path', 'Unknown')}")
            console.print(f"   📦 Version: {result.get('cli_version', 'Unknown')}")

            # Check libraries
            if result.get("libraries_available", False):
                console.print(
                    f"   📚 Symbol libraries: {result.get('symbol_path', 'Not found')}"
                )
                console.print(
                    f"   👟 Footprint libraries: {result.get('footprint_path', 'Not found')}"
                )
            else:
                console.print(
                    "   ⚠️  Libraries not found but CLI available", style="yellow"
                )

            result["kicad_installed"] = True
            return result
        else:
            console.print("❌ KiCad not found", style="red")
            console.print("📥 Install options:", style="cyan")

            # Cross-platform installation suggestions
            if sys.platform == "darwin":  # macOS
                console.print("   • Download: https://www.kicad.org/download/macos/")
                console.print("   • Homebrew: brew install kicad")
            elif sys.platform == "win32":  # Windows
                console.print("   • Download: https://www.kicad.org/download/windows/")
                console.print("   • Chocolatey: choco install kicad")
                console.print("   • Winget: winget install KiCad.KiCad")
            else:  # Linux
                console.print("   • Download: https://www.kicad.org/download/linux/")
                console.print("   • Ubuntu/Debian: sudo apt install kicad")
                console.print("   • Fedora: sudo dnf install kicad")
                console.print("   • Arch: sudo pacman -S kicad")

            result["kicad_installed"] = False
            return result

    except Exception as e:
        console.print(f"⚠️  Could not verify KiCad installation: {e}", style="yellow")
        return {"kicad_installed": False, "error": str(e)}


def copy_example_project_template(project_path: Path) -> bool:
    """Copy the entire example_project template to the target project directory

    Returns:
        bool: True if template was successfully copied, False otherwise
    """

    # Find the project template in the package data directory
    circuit_synth_dir = Path(
        __file__
    ).parent.parent.parent  # Get to circuit_synth directory
    template_dir = circuit_synth_dir / "data" / "templates" / "example_project"

    # Fallback: check for example_project in repo root (for development)
    if not template_dir.exists():
        circuit_synth_root = Path(__file__).parent.parent.parent.parent
        fallback_template = circuit_synth_root / "example_project"
        if fallback_template.exists():
            template_dir = fallback_template

    if not template_dir.exists():
        console.print(
            f"⚠️  Project template not found at {template_dir}", style="yellow"
        )
        console.print("🔄 Falling back to basic project creation", style="yellow")
        return False

    console.print(
        f"📋 Copying complete project template from {template_dir}", style="blue"
    )

    try:
        # Copy all files and directories from template to project_path
        for item in template_dir.iterdir():
            if item.is_file():
                # Copy individual files
                dest_file = project_path / item.name
                shutil.copy2(item, dest_file)
                console.print(f"   ✅ Copied {item.name}", style="green")
            elif item.is_dir():
                # Copy entire directories
                dest_dir = project_path / item.name
                if dest_dir.exists():
                    shutil.rmtree(dest_dir)
                shutil.copytree(item, dest_dir)
                console.print(f"   ✅ Copied {item.name}/ directory", style="green")

        console.print("✅ Complete project template copied successfully", style="green")
        console.print(
            "   🎯 Ready-to-use ESP32-C6 development board example included!",
            style="cyan",
        )
        console.print(
            "   🤖 Claude Code agents and commands included from template!",
            style="cyan",
        )
        return True

    except Exception as e:
        console.print(f"⚠️  Could not copy project template: {e}", style="yellow")
        console.print(
            "🔄 Project setup will continue without template files", style="yellow"
        )
        return False


def create_project_readme(
    project_path: Path, project_name: str, additional_libraries: List[str]
) -> None:
    """Create project README with circuit-synth usage guide"""

    readme_content = f"""# {project_name}

A circuit-synth project for professional circuit design with hierarchical architecture.

## 🚀 Quick Start

```bash
# Run the ESP32-C6 development board example
uv run python circuit-synth/main.py
```

## 📁 Project Structure

```
my_kicad_project/
├── circuit-synth/        # Circuit-synth Python files
│   ├── main.py           # Main ESP32-C6 development board (nets only)
│   ├── usb_subcircuit.py # USB-C with CC resistors and ESD protection
│   ├── power_supply_subcircuit.py # 5V to 3.3V power regulation
│   ├── debug_header_subcircuit.py # Programming and debug interface
│   ├── led_blinker_subcircuit.py  # Status LED with current limiting
│   └── esp32_subcircuit.py        # ESP32-C6 microcontroller subcircuit
├── kicad_plugins/        # KiCad plugin files for AI integration
│   ├── circuit_synth_bom_plugin.py        # Schematic BOM plugin
│   ├── circuit_synth_pcb_bom_bridge.py   # PCB editor plugin
│   ├── install_plugin.py                 # Plugin installer script
│   └── README_SIMPLIFIED.md              # Plugin setup instructions
├── kicad-project/        # KiCad files (generated when circuits run)
│   ├── ESP32_C6_Dev_Board.kicad_pro        # Main project file
│   ├── ESP32_C6_Dev_Board.kicad_sch        # Top-level schematic  
│   ├── ESP32_C6_Dev_Board.kicad_pcb        # PCB layout
│   ├── USB_Port.kicad_sch                  # USB-C circuit sheet
│   ├── Power_Supply.kicad_sch              # Power regulation circuit sheet
│   ├── Debug_Header.kicad_sch              # Debug interface circuit sheet
│   └── LED_Blinker.kicad_sch               # Status LED circuit sheet
├── .claude/              # AI agents for Claude Code
│   ├── agents/           # Specialized circuit design agents
│   └── commands/         # Slash commands
├── README.md            # This file
└── CLAUDE.md            # Project-specific Claude guidance
```

## 🏗️ Circuit-Synth Basics

### **Hierarchical Design Philosophy**

Circuit-synth uses **hierarchical subcircuits** - each subcircuit is like a software function with single responsibility and clear interfaces. **The main circuit only defines nets and passes them to subcircuits:**

```python
@circuit(name="ESP32_C6_Dev_Board_Main")
def main_circuit():
    \"\"\"Main circuit - ONLY nets and subcircuit connections\"\"\"
    # Define shared nets (no components here!)
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    usb_dp = Net('USB_DP')
    
    # Pass nets to subcircuits
    esp32 = esp32_subcircuit(vcc_3v3, gnd, usb_dp, ...)
    power_supply = power_supply_subcircuit()
```

### **Basic Component Creation**

```python
# Create components with symbol, reference, and footprint
mcu = Component(
    symbol="RF_Module:ESP32-C6-MINI-1",       # KiCad symbol
    ref="U",                                   # Reference prefix  
    footprint="RF_Module:ESP32-C6-MINI-1"
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

1. **Design**: Create hierarchical circuits in Python
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
3. Create your own hierarchical circuits
4. Validate designs with SPICE simulation
5. Generate production-ready KiCad projects

**Happy circuit designing!** 🎛️
"""

    with open(project_path / "README.md", "w") as f:
        f.write(readme_content)

    console.print(f"✅ Created project README.md", style="green")


def create_claude_md(project_path: Path) -> None:
    """Create project-specific CLAUDE.md file with circuit-synth guidance"""

    claude_md_content = f"""# CLAUDE.md

Project-specific guidance for Claude Code when working with this circuit-synth project.

## 🚀 Project Overview

This is a **circuit-synth project** for professional circuit design with AI-powered component intelligence.

## ⚡ Available Tools & Commands

### **Slash Commands**
- `/find-symbol STM32` - Search KiCad symbol libraries
- `/find-footprint LQFP` - Search KiCad footprint libraries  
- `/analyze-design` - Analyze circuit designs
- `/find_stm32` - STM32-specific component search
- `/generate_circuit` - Circuit generation workflows

### **Specialized Agents** 
- **orchestrator** - Master coordinator for complex projects
- **circuit-synth** - Circuit code generation and KiCad integration
- **simulation-expert** - SPICE simulation and validation
- **jlc-parts-finder** - JLCPCB component availability and sourcing
- **general-purpose** - Research and codebase analysis
- **code** - Software engineering and code quality

## 🏗️ Development Workflow

### **1. Component-First Design**
Always start with component availability checking:
```
👤 "Find STM32 with 3 SPIs available on JLCPCB"
👤 "Search for low-power op-amps suitable for battery applications"
```

### **2. Circuit Generation**
Use agents for code generation:
```
👤 @Task(subagent_type="circuit-synth", description="Create power supply", 
     prompt="Design 3.3V regulator circuit with USB-C input and overcurrent protection")
```

### **3. Validation & Simulation**
Validate designs before manufacturing:
```
👤 @Task(subagent_type="simulation-expert", description="Validate filter", 
     prompt="Simulate this low-pass filter and optimize component values")
```

## 🔧 Essential Commands

```bash
# Run the main example
uv run python circuit-synth/main.py

# Test the setup
uv run python -c "from circuit_synth import *; print('✅ Circuit-synth ready!')"
```

## 🔌 KiCad Plugin Setup (Optional AI Integration)

Circuit-synth includes optional KiCad plugins for AI-powered circuit analysis:

```bash
# Install KiCad plugins (separate command)
uv run cs-setup-kicad-plugins
```

After installation and restarting KiCad:
- **PCB Editor**: Tools → External Plugins → "Circuit-Synth AI"  
- **Schematic Editor**: Tools → Generate Bill of Materials → "Circuit-Synth AI"

The plugins provide AI-powered BOM analysis and component optimization directly within KiCad!

## 🎯 Best Practices

### **Component Selection Priority**
1. **JLCPCB availability first** - Always check stock levels
2. **Standard packages** - Prefer common footprints (0603, 0805, LQFP)
3. **Proven components** - Use established parts with good track records

### **Circuit Organization**
- **Hierarchical design** - Use circuits for complex designs
- **Clear interfaces** - Define nets and connections explicitly  
- **Manufacturing focus** - Design for assembly and testing

### **AI Agent Usage**
- **Start with orchestrator** for complex multi-step projects
- **Use circuit-synth** for component selection and code generation
- **Use simulation-expert** for validation and optimization
- **Use jlc-parts-finder** for sourcing and alternatives

## 📚 Quick Reference

### **Component Creation**
```python
mcu = Component(
    symbol="RF_Module:ESP32-C6-MINI-1",
    ref="U",
    footprint="RF_Module:ESP32-C6-MINI-1"
)
```

### **Net Connections**
```python
vcc = Net("VCC_3V3")
mcu["VDD"] += vcc
```

### **Circuit Generation**
```python
@circuit(name="Power_Supply")
def power_supply():
    # Circuit implementation
    pass
```

## 🚀 Getting Help

- Use **natural language** to describe what you want to build
- **Be specific** about requirements (voltage, current, package, etc.)
- **Ask for alternatives** when components are out of stock
- **Request validation** for critical circuits before manufacturing

**Example project requests:**
```
👤 "Design ESP32 IoT sensor node with LoRaWAN, solar charging, and environmental sensors"
👤 "Create USB-C PD trigger circuit for 20V output with safety protection" 
👤 "Build ESP32-based IoT sensor node with WiFi, environmental sensors, and battery management"
```

---

**This project is optimized for AI-powered circuit design with Claude Code!** 🎛️
"""

    claude_md_file = project_path / "CLAUDE.md"
    with open(claude_md_file, "w") as f:
        f.write(claude_md_content)

    console.print(f"✅ Created project CLAUDE.md", style="green")


@click.command()
@click.option("--skip-kicad-check", is_flag=True, help="Skip KiCad installation check")
@click.option("--quick", is_flag=True, help="Quick start with defaults (no prompts)")
@click.option("--circuits", type=str, help="Comma-separated circuits: resistor,led,esp32,usb")
@click.option("--no-agents", is_flag=True, help="Skip Claude AI agents setup")
@click.option("--developer", is_flag=True, help="Include developer tools")
def main(skip_kicad_check: bool, quick: bool, circuits: Optional[str],
         no_agents: bool, developer: bool):
    """Setup circuit-synth in the current uv project directory

    Run this command from within your uv project directory after:
    1. uv init my-project
    2. cd my-project
    3. uv add circuit-synth
    4. uv run cs-new-project

    Examples:
        # Interactive mode (default) - shows menu to select circuits
        uv run cs-new-project

        # Quick start with defaults (resistor divider)
        uv run cs-new-project --quick

        # Select specific circuits via flags
        uv run cs-new-project --circuits resistor,led,esp32

        # Minimal project without Claude agents
        uv run cs-new-project --circuits minimal --no-agents
    """

    # Use current directory as project path
    project_path = Path.cwd()

    # Remove default main.py created by uv init (we don't need it)
    default_main = project_path / "main.py"
    if default_main.exists():
        default_main.unlink()

    # Step 1: Check KiCad installation (unless skipped)
    kicad_installed = False
    if not skip_kicad_check:
        kicad_info = check_kicad_installation()
        kicad_installed = kicad_info.get("kicad_installed", False)
        if not kicad_installed:
            if not Confirm.ask(
                "Continue without KiCad? (You'll need it later for opening projects)"
            ):
                console.print("❌ Aborted - Please install KiCad first", style="red")
                sys.exit(1)

    # Step 2: Determine project configuration
    config = None

    if quick:
        # Quick mode: use defaults, no prompts
        console.print("[bold cyan]⚡ Quick Start Mode[/bold cyan]")
        config = get_default_config()
        if developer:
            config.developer_mode = True
        console.print(f"✅ Creating project with: [green]{', '.join([c.display_name for c in config.circuits])}[/green]")
        console.print()

    elif circuits or no_agents:
        # Flag-based mode: parse flags into configuration
        config = parse_cli_flags(circuits, no_agents, developer)
        if config is None:
            sys.exit(1)  # parse_cli_flags already printed error

    else:
        # Interactive mode: run interactive CLI
        config = run_interactive_setup(project_path, developer_mode=developer)
        if config is None:
            console.print("[yellow]Setup cancelled by user[/yellow]")
            sys.exit(0)

    # Step 3: Initialize template manager and generators
    template_mgr = TemplateManager()
    readme_gen = READMEGenerator()
    claude_md_gen = CLAUDEMDGenerator()

    # Step 4: Create circuit-synth directory and copy all selected circuits
    console.print("\n[bold cyan]📝 Creating Project Files...[/bold cyan]")

    if config.has_circuits():
        for idx, circuit in enumerate(config.circuits):
            try:
                # First circuit becomes main.py, others use their own names
                is_first = (idx == 0)
                template_mgr.copy_circuit_to_project(circuit, project_path, is_first=is_first)

                if is_first:
                    console.print(f"✅ Created circuit-synth/main.py ({circuit.display_name})", style="green")
                else:
                    console.print(f"✅ Created circuit-synth/{circuit.value}.py ({circuit.display_name})", style="green")

            except FileNotFoundError as e:
                console.print(f"[yellow]⚠️  Could not add {circuit.display_name}: {e}[/yellow]")
    else:
        console.print("[yellow]⚠️  No circuits selected. Creating empty project.[/yellow]")

    # Step 6: Setup Claude AI agents if requested
    if config.include_agents:
        console.print("\n[cyan]🤖 Setting up Claude Code integration...[/cyan]")
        try:
            copy_complete_claude_setup(project_path, developer_mode=config.developer_mode)
            agents_count = len(list((project_path / '.claude' / 'agents').rglob('*.md')))
            commands_count = len(list((project_path / '.claude' / 'commands').rglob('*.md')))
            console.print(f"✅ Claude agents setup complete ({agents_count} agents, {commands_count} commands)", style="green")
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not setup Claude agents: {e}[/yellow]")
    else:
        console.print("\n[dim]⏭️  Skipped Claude agents setup[/dim]")

    # Step 7: Generate README.md and CLAUDE.md
    console.print("\n[cyan]📚 Generating documentation...[/cyan]")

    readme_content = readme_gen.generate(config, project_path)
    readme_path = project_path / "README.md"
    readme_path.write_text(readme_content)
    console.print("✅ Created README.md", style="green")

    claude_md_content = claude_md_gen.generate(config)
    claude_md_path = project_path / "CLAUDE.md"
    claude_md_path.write_text(claude_md_content)
    console.print("✅ Created CLAUDE.md", style="green")

    # Step 8: KiCad plugins note (if KiCad is installed)
    if kicad_installed:
        console.print("\n[cyan]🔌 KiCad plugins available separately[/cyan]")
        console.print("[dim]   Run 'uv run cs-setup-kicad-plugins' to install AI integration plugins[/dim]")

    # Success message
    console.print()
    success_text = (
        Text(f"✅ Circuit-synth project setup complete!", style="bold green")
        + Text(f"\n\n📁 Location: {project_path}")
    )

    if config.has_circuits():
        circuits_names = ', '.join([c.display_name for c in config.circuits])
        success_text += Text(f"\n🎛️  Circuits ({len(config.circuits)}): {circuits_names}")

    success_text += Text(f"\n\n🚀 Get started: [cyan]uv run python circuit-synth/main.py[/cyan]")
    success_text += Text(f"\n📖 Documentation: See README.md")

    if config.include_agents:
        agents_count = len(list((project_path / '.claude' / 'agents').rglob('*.md')))
        commands_count = len(list((project_path / '.claude' / 'commands').rglob('*.md')))
        success_text += Text(f"\n🤖 AI Agents: {agents_count} agents, {commands_count} commands available")

    console.print(Panel.fit(success_text, title="🎉 Success!", style="green"))


if __name__ == "__main__":
    main()
