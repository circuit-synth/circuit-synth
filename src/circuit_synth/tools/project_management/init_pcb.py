#!/usr/bin/env python3
"""
Circuit-Synth PCB Initialization Tool

Adds circuit-synth to an existing KiCad project by:
1. Creating circuit-synth/, memory-bank/, and .claude/ directories
2. Converting KiCad schematic to Python code (optional)
3. Setting up PCB-specific Claude AI agent
4. Integrating memory-bank system

Usage:
    cs-init-pcb                    # Initialize in current directory
    cs-init-pcb /path/to/project   # Initialize in specific directory
"""

import os
import shutil
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.text import Text

# Import circuit-synth modules
from circuit_synth.ai_integration.memory_bank import MemoryBankManager

console = Console()


def find_kicad_files(directory: Path) -> dict:
    """Find KiCad files in directory."""
    kicad_files = {
        "project": None,
        "schematic": [],
        "pcb": None,
        "netlist": [],
        "other": [],
    }

    for file in directory.iterdir():
        if file.suffix == ".kicad_pro":
            kicad_files["project"] = file
        elif file.suffix == ".kicad_sch":
            kicad_files["schematic"].append(file)
        elif file.suffix == ".kicad_pcb":
            kicad_files["pcb"] = file
        elif file.suffix == ".net":
            kicad_files["netlist"].append(file)
        elif file.suffix in [".json", ".bak"]:  # Other KiCad-related files
            kicad_files["other"].append(file)

    return kicad_files


def organize_kicad_files(project_path: Path, kicad_files: dict) -> dict:
    """Move KiCad files to organized kicad/ directory."""

    # Create kicad directory
    kicad_dir = project_path / "kicad"
    kicad_dir.mkdir(exist_ok=True)

    new_locations = {
        "project": None,
        "schematic": [],
        "pcb": None,
        "netlist": [],
        "other": [],
    }

    # Move files to kicad/ directory
    for file_type, files in kicad_files.items():
        if file_type == "project" and files:
            new_path = kicad_dir / files.name
            if not new_path.exists():
                shutil.move(str(files), str(new_path))
            new_locations["project"] = new_path
        elif file_type in ["schematic", "netlist", "other"] and files:
            for file in files:
                new_path = kicad_dir / file.name
                if not new_path.exists():
                    shutil.move(str(file), str(new_path))
                new_locations[file_type].append(new_path)
        elif file_type == "pcb" and files:
            new_path = kicad_dir / files.name
            if not new_path.exists():
                shutil.move(str(files), str(new_path))
            new_locations["pcb"] = new_path

    console.print("✅ Organized KiCad files into kicad/ directory", style="green")
    return new_locations


def create_circuit_synth_structure(
    project_path: Path, project_name: str, kicad_dir: str = "kicad"
) -> None:
    """Create circuit-synth directory structure with complete working example."""

    # Create circuit-synth directory
    circuit_synth_dir = project_path / "circuit-synth"
    circuit_synth_dir.mkdir(exist_ok=True)

    # Find the example_project directory (relative to this script)
    current_file = Path(__file__)
    repo_root = current_file.parent.parent.parent.parent  # Go up to circuit-synth4/
    example_project_dir = repo_root / "example_project" / "circuit-synth"

    if not example_project_dir.exists():
        # Fallback to simple template if examples not found
        console.print(
            "⚠️  Example project not found, creating simple template", style="yellow"
        )
        _create_simple_template(circuit_synth_dir, project_name, kicad_dir)
        return

    # Copy all circuit files from example project
    circuit_files = [
        "usb.py",
        "power_supply.py",
        "esp32c6.py",
        "debug_header.py",
        "led_blinker.py",
    ]

    for circuit_file in circuit_files:
        source_file = example_project_dir / circuit_file
        if source_file.exists():
            dest_file = circuit_synth_dir / circuit_file
            shutil.copy2(str(source_file), str(dest_file))

    # Create customized main.py for this project
    main_py_content = f'''#!/usr/bin/env python3
"""
Main Circuit - {project_name}
Professional hierarchical circuit design with modular subcircuits

This is the main entry point that orchestrates all subcircuits:
- USB-C power input with proper CC resistors and protection
- 5V to 3.3V power regulation  
- ESP32-C6 microcontroller with USB and debug interfaces
- Status LED with current limiting
- Debug header for programming and development
"""

from circuit_synth import *

# Import all circuits
from usb import usb_port
from power_supply import power_supply
from esp32c6 import esp32c6

@circuit(name="{project_name.replace(' ', '_')}_Main")
def main_circuit():
    """Main hierarchical circuit - {project_name}"""
    
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
    print("Starting {project_name.replace('_', ' ')} generation...")
    
    # Generate the complete hierarchical circuit
    print("Creating circuit...")
    circuit = main_circuit()
    
    # Generate KiCad netlist (required for ratsnest display) - save to kicad project folder
    print("Generating KiCad netlist...")
    circuit.generate_kicad_netlist("../kicad/{project_name.replace(' ', '_')}.net")
    
    # Generate JSON netlist (for debugging and analysis) - save to circuit-synth folder
    print("Generating JSON netlist...")
    circuit.generate_json_netlist("{project_name.replace(' ', '_')}.json")
    
    # Create KiCad project with hierarchical sheets
    print("Generating KiCad project...")
    circuit.generate_kicad_project(
        project_name="{project_name.replace(' ', '_')}",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    
    print("")
    print("{project_name} project generated!")
    print("Check the ../kicad/ directory for KiCad files")
    print("")
    print("Generated circuits:")
    print("   • USB-C port with CC resistors and ESD protection")
    print("   • 5V to 3.3V power regulation")
    print("   • ESP32-C6 microcontroller with support circuits")
    print("   • Debug header for programming")  
    print("   • Status LED with current limiting")
    print("")
    print("Generated files:")
    print("   • {project_name.replace(' ', '_')}.kicad_pro - KiCad project file")
    print("   • {project_name.replace(' ', '_')}.kicad_sch - Hierarchical schematic")
    print("   • {project_name.replace(' ', '_')}.kicad_pcb - PCB layout")
    print("   • {project_name.replace(' ', '_')}.net - Netlist (enables ratsnest)")
    print("   • {project_name.replace(' ', '_')}.json - JSON netlist (for analysis)")
    print("")
    print("Ready for professional PCB manufacturing!")
    print("Open ../kicad/{project_name.replace(' ', '_')}.kicad_pcb in KiCad to see the ratsnest!")
'''

    with open(circuit_synth_dir / "main.py", "w") as f:
        f.write(main_py_content)

    console.print(
        "✅ Created circuit-synth/ directory with complete working example",
        style="green",
    )


def _create_simple_template(
    circuit_synth_dir: Path, project_name: str, kicad_dir: str
) -> None:
    """Fallback: Create simple template if example project not found."""

    main_py_content = f'''#!/usr/bin/env python3
"""
{project_name} - Circuit-Synth Integration

This file was created by cs-init-pcb to integrate circuit-synth with your existing KiCad project.
"""

from circuit_synth import *

@circuit(name="{project_name.replace(' ', '_')}")
def {project_name.lower().replace(' ', '_').replace('-', '_')}_circuit():
    """
    Main circuit converted from KiCad project.
    
    TODO: Add your circuit-synth components here, or run KiCad-to-Python conversion.
    """
    
    # Example: Create nets
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    
    # TODO: Add your components here
    # Example:
    # mcu = Component(
    #     symbol="MCU_ST_STM32F4:STM32F407VETx",
    #     ref="U",
    #     footprint="Package_QFP:LQFP-100_14x14mm_P0.5mm"
    # )
    
    print("🚧 Circuit structure ready for implementation")
    return circuit


if __name__ == "__main__":
    print("🚀 Generating {project_name}...")
    
    # Generate the circuit
    circuit = {project_name.lower().replace(' ', '_').replace('-', '_')}_circuit()
    
    # Generate KiCad project (updates existing files in kicad/ directory)
    circuit.generate_kicad_project("{project_name.replace(' ', '_')}", output_dir="../{kicad_dir}")
    
    print("✅ {project_name} circuit-synth integration complete!")
    print("📁 Edit circuit-synth/main.py to add your components")
    print("📁 KiCad files are organized in {kicad_dir}/ directory")
    print("📖 See README.md for next steps")
'''

    with open(circuit_synth_dir / "main.py", "w") as f:
        f.write(main_py_content)


def create_memory_bank(project_path: Path, project_name: str) -> None:
    """Create memory-bank system."""

    memory_bank_dir = project_path / "memory-bank"
    memory_bank_dir.mkdir(exist_ok=True)

    # Cache directory
    cache_dir = memory_bank_dir / "cache"
    cache_dir.mkdir(exist_ok=True)

    # Standard memory-bank files (same as new_pcb.py)
    templates = {
        "decisions.md": f"""# Design Decisions - {project_name}

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
        "fabrication.md": f"""# Fabrication History - {project_name}

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
        "testing.md": f"""# Testing Results - {project_name}

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
        "timeline.md": f"""# Project Timeline - {project_name}

*This file tracks project milestones, key events, and deadlines*

## Template Milestone
**Date**: YYYY-MM-DD  
**Milestone**: Brief description of milestone or event  
**Status**: Completed, In Progress, Planned  
**Details**: Additional context and notes  
**Next Steps**: What needs to happen next  

---

""",
        "issues.md": f"""# Issues & Solutions - {project_name}

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

""",
    }

    for filename, content in templates.items():
        file_path = memory_bank_dir / filename
        with open(file_path, "w") as f:
            f.write(content)

    console.print("✅ Created memory-bank system", style="green")


def create_claude_agent(project_path: Path, project_name: str) -> None:
    """Create PCB-specific Claude agent configuration with complete agent system."""

    claude_dir = project_path / ".claude"
    claude_dir.mkdir(exist_ok=True)

    # Find the example_project .claude directory (relative to this script)
    current_file = Path(__file__)
    repo_root = current_file.parent.parent.parent.parent  # Go up to circuit-synth4/
    example_claude_dir = repo_root / "example_project" / ".claude"

    if example_claude_dir.exists():
        # Copy agents directory
        agents_source = example_claude_dir / "agents"
        agents_dest = claude_dir / "agents"
        if agents_source.exists():
            shutil.copytree(str(agents_source), str(agents_dest), dirs_exist_ok=True)

        # Copy commands directory
        commands_source = example_claude_dir / "commands"
        commands_dest = claude_dir / "commands"
        if commands_source.exists():
            shutil.copytree(
                str(commands_source), str(commands_dest), dirs_exist_ok=True
            )

        # Copy all additional configuration files
        config_files = [
            "README.md",
            "settings.json",
            "AGENT_USAGE_GUIDE.md",
            "README_ORGANIZATION.md",
            "mcp_settings.json",
            "session_hook_update.sh",
        ]
        for filename in config_files:
            source_file = example_claude_dir / filename
            if source_file.exists():
                dest_file = claude_dir / filename
                shutil.copy2(str(source_file), str(dest_file))

    # Create customized instructions.md for this specific project
    instructions_content = f"""# {project_name} PCB Agent

You are a specialized circuit design assistant working on the {project_name} PCB.

## Memory-Bank Integration

Automatically update memory-bank files in ./memory-bank/:
- **decisions.md**: Component choices and design rationale
- **fabrication.md**: PCB orders, delivery, assembly notes
- **testing.md**: Test results, measurements, validation
- **timeline.md**: Project milestones and key events
- **issues.md**: Problems encountered and solutions

## Context

- **PCB**: {project_name}
- **Circuit Files**: ./circuit-synth/
- **KiCad Files**: ./kicad/ (organized in separate directory)
- **Memory-Bank**: ./memory-bank/

## Existing Project Integration

This PCB was initialized from an existing KiCad project using cs-init-pcb.
- Help convert KiCad schematics to circuit-synth Python code
- Maintain compatibility between KiCad files and circuit-synth
- Provide guidance on incremental migration strategies

## Automatic Documentation

Update memory-bank when:
- Git commits are made (primary trigger)
- Component changes occur
- Tests are performed  
- Issues are encountered
- Fabrication orders are placed

## Expertise

- Circuit-synth code generation from KiCad schematics
- KiCad ↔ circuit-synth synchronization
- Component selection and verification
- Manufacturing considerations (JLCPCB focus)
- PCB design best practices
- Incremental migration from pure KiCad to circuit-synth hybrid workflow

## Available Agents

Use the specialized agents in ./agents/ for specific tasks:
- **circuit-architect**: Master circuit design coordinator
- **circuit-synth**: Circuit-synth code generation specialist  
- **component-guru**: Manufacturing and sourcing specialist
- **jlc-parts-finder**: JLCPCB component search and verification
- **simulation-expert**: SPICE simulation and validation
- **stm32-mcu-finder**: STM32 microcontroller selection

## Available Commands

Use the slash commands in ./commands/ for quick tasks:
- **/find-symbol**: Search KiCad symbol libraries
- **/find-footprint**: Search KiCad footprint libraries
- **/find-mcu**: Find microcontrollers with specific features
- **/generate-circuit**: Generate circuit-synth code from description
- **/analyze-design**: Analyze circuit design and suggest improvements
"""

    with open(claude_dir / "instructions.md", "w") as f:
        f.write(instructions_content)

    if example_claude_dir.exists():
        console.print(
            "✅ Created complete Claude agent system with all agents and commands",
            style="green",
        )
    else:
        console.print(
            "✅ Created Claude agent configuration (example agents not found)",
            style="green",
        )


def create_readme(project_path: Path, project_name: str, kicad_files: dict) -> None:
    """Create README for existing project integration."""

    kicad_file_list = []
    if kicad_files["project"]:
        kicad_file_list.append(
            f"│   ├── {kicad_files['project'].name}     # KiCad project"
        )
    for schematic in kicad_files["schematic"]:
        kicad_file_list.append(f"│   ├── {schematic.name}   # KiCad schematic")
    if kicad_files["pcb"]:
        kicad_file_list.append(f"│   ├── {kicad_files['pcb'].name}        # KiCad PCB")
    for netlist in kicad_files["netlist"]:
        kicad_file_list.append(f"│   ├── {netlist.name}             # KiCad netlist")
    for other in kicad_files["other"]:
        kicad_file_list.append(f"│   ├── {other.name}             # KiCad misc")

    readme_content = f"""# {project_name}

A KiCad project enhanced with circuit-synth integration.

## Quick Start

```bash
# Edit Python circuit definition
nano circuit-synth/main.py

# Generate/update KiCad files from Python
cd circuit-synth && uv run python main.py
```

## Project Structure

```
{project_name.lower().replace(' ', '-')}/
├── kicad/             # KiCad design files
{''.join(kicad_file_list)}
├── circuit-synth/     # Python circuit files
├── memory-bank/       # Automatic documentation
└── .claude/           # AI assistant configuration
```

## Integration Workflow

This project was initialized with `cs-init-pcb` from an existing KiCad design.

### Option 1: KiCad → Circuit-Synth Conversion
1. Use KiCad-to-Python converter (if available) to generate initial circuit-synth code
2. Edit `circuit-synth/main.py` to match your KiCad schematic
3. Use circuit-synth as the source of truth going forward

### Option 2: Hybrid Workflow  
1. Continue using KiCad for schematic editing
2. Use circuit-synth for specific tasks (component selection, variant generation)
3. Keep both tools synchronized manually

### Option 3: Gradual Migration
1. Start with simple circuits in circuit-synth
2. Gradually migrate more complex sections
3. Eventually use circuit-synth as primary design tool

## Memory-Bank System

This PCB uses automatic documentation that tracks:
- Design decisions and component choices
- Fabrication orders and assembly notes  
- Test results and measurements
- Project timeline and milestones
- Issues and solutions

## AI Assistant

This PCB has a dedicated Claude AI agent configured for:
- KiCad ↔ circuit-synth integration assistance
- Component selection and verification
- Design review and optimization suggestions
- Memory-bank maintenance
"""

    with open(project_path / "README.md", "w") as f:
        f.write(readme_content)

    console.print("✅ Created integration README.md", style="green")


@click.command()
@click.argument("project_path", default=".", type=click.Path(exists=True))
def main(project_path: str):
    """Initialize circuit-synth in an existing KiCad project.

    PROJECT_PATH: Directory containing KiCad files (default: current directory)

    Examples:
        cs-init-pcb                    # Initialize in current directory
        cs-init-pcb ./my-kicad-project # Initialize in specific directory
    """

    project_dir = Path(project_path).resolve()

    console.print(
        Panel.fit(
            Text(
                f"🚀 Initializing circuit-synth in: {project_dir.name}",
                style="bold blue",
            ),
            style="blue",
        )
    )

    # Find KiCad files
    kicad_files = find_kicad_files(project_dir)

    if not any(kicad_files.values()):
        console.print("❌ No KiCad files found in directory", style="red")
        console.print(
            "💡 Expected files: .kicad_pro, .kicad_sch, or .kicad_pcb", style="yellow"
        )
        sys.exit(1)

    # Show found files
    console.print("📁 Found KiCad files:", style="green")
    if kicad_files["project"]:
        console.print(f"   ✓ project: {kicad_files['project'].name}", style="green")
    else:
        console.print(f"   - project: not found", style="dim")

    if kicad_files["schematic"]:
        for sch in kicad_files["schematic"]:
            console.print(f"   ✓ schematic: {sch.name}", style="green")
    else:
        console.print(f"   - schematic: not found", style="dim")

    if kicad_files["pcb"]:
        console.print(f"   ✓ pcb: {kicad_files['pcb'].name}", style="green")
    else:
        console.print(f"   - pcb: not found", style="dim")

    # Get project name
    if kicad_files["project"]:
        project_name = kicad_files["project"].stem
    elif kicad_files["schematic"]:
        project_name = kicad_files["schematic"][0].stem
    else:
        project_name = project_dir.name

    console.print(f"📋 Project name: {project_name}", style="blue")

    # Check if circuit-synth already initialized
    if (project_dir / "circuit-synth").exists():
        console.print("⚠️  circuit-synth directory already exists", style="yellow")
        if not Confirm.ask("Continue and overwrite?"):
            console.print("❌ Initialization cancelled", style="red")
            sys.exit(1)

    # Create structure
    console.print("\n🏗️  Setting up circuit-synth integration...", style="yellow")

    try:
        # Organize KiCad files first
        console.print("\n📁 Organizing KiCad files...", style="yellow")
        organized_kicad_files = organize_kicad_files(project_dir, kicad_files)

        # Create circuit-synth structure
        create_circuit_synth_structure(project_dir, project_name)

        # Create memory-bank system
        console.print("\n🧠 Setting up memory-bank system...", style="yellow")
        create_memory_bank(project_dir, project_name)

        # Create Claude agent
        console.print("\n🤖 Setting up AI assistant...", style="yellow")
        create_claude_agent(project_dir, project_name)

        # Create README
        console.print("\n📚 Creating documentation...", style="yellow")
        create_readme(project_dir, project_name, organized_kicad_files)

        # Success message
        console.print(
            Panel.fit(
                Text(
                    f"✅ Circuit-synth initialized for '{project_name}'!",
                    style="bold green",
                )
                + Text(f"\n\n📁 Location: {project_dir}")
                + Text(f"\n🚀 Next steps:")
                + Text(f"\n   1. Edit circuit-synth/main.py to define your circuit")
                + Text(f"\n   2. Run: cd circuit-synth && uv run python main.py")
                + Text(f"\n   3. See README.md for integration strategies")
                + Text(f"\n\n📁 KiCad files: Organized in kicad/ directory")
                + Text(f"\n🧠 Memory-bank: Automatic documentation enabled")
                + Text(f"\n🤖 AI Agent: PCB-specific Claude assistant configured"),
                title="🎉 Success!",
                style="green",
            )
        )

    except Exception as e:
        console.print(f"❌ Error during initialization: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    main()
