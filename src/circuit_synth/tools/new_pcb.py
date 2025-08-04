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
# from circuit_synth.memory_bank import MemoryBankManager  # TODO: implement when memory bank is ready

console = Console()


def create_full_hierarchical_examples(pcb_path: Path, pcb_name: str) -> None:
    """Copy the complete example project using safe file-by-file copying."""
    # Get absolute paths to avoid any recursion issues
    current_file = Path(__file__).resolve()
    repo_root = current_file.parent.parent.parent.parent
    example_circuit_dir = repo_root / "example_project" / "circuit-synth"
    target_circuit_dir = pcb_path.resolve() / "circuit-synth"
    
    if not example_circuit_dir.exists():
        console.print(f"[red]Warning: Example project not found at {example_circuit_dir}[/red]")
        console.print("[yellow]Falling back to basic circuit generation...[/yellow]")
        _create_basic_circuits(pcb_path, pcb_name)
        return
    
    # Create target directory
    target_circuit_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy Python files individually to avoid recursion
    python_files = ["main.py", "debug_header.py", "esp32c6.py", "led_blinker.py", "power_supply.py", "usb.py"]
    for file_name in python_files:
        source_file = example_circuit_dir / file_name
        target_file = target_circuit_dir / file_name
        if source_file.exists():
            shutil.copy2(source_file, target_file)
    
    # Copy JSON file if it exists
    json_file = example_circuit_dir / "ESP32_C6_Dev_Board.json"
    if json_file.exists():
        shutil.copy2(json_file, target_circuit_dir / "ESP32_C6_Dev_Board.json")
    
    # Copy KiCad directory if it exists
    example_kicad_dir = example_circuit_dir / "ESP32_C6_Dev_Board"
    if example_kicad_dir.exists():
        target_kicad_dir = pcb_path.resolve() / "ESP32_C6_Dev_Board"
        if target_kicad_dir.exists():
            shutil.rmtree(target_kicad_dir)
        shutil.copytree(example_kicad_dir, target_kicad_dir)
        console.print(f"[green]✅ Copied KiCad project files from example[/green]")
    
    # Update the main.py file to use the new PCB name
    main_py = target_circuit_dir / "main.py"
    if main_py.exists():
        content = main_py.read_text()
        # Replace the circuit name in the decorator
        updated_content = content.replace('@circuit(name="ESP32_C6_Dev_Board")', f'@circuit(name="{pcb_name.replace(" ", "_")}")')
        # Update any title/description comments
        updated_content = updated_content.replace("ESP32-C6 Development Board", pcb_name)
        updated_content = updated_content.replace("ESP32_C6_Dev_Board", pcb_name.replace(" ", "_"))
        main_py.write_text(updated_content)
    
    console.print(f"[green]✅ Copied proven circuit examples from example_project[/green]")


def _create_basic_circuits(pcb_path: Path, pcb_name: str) -> None:
    """Fallback: Create basic circuits if example project is not available."""
    circuit_synth_dir = pcb_path / "circuit-synth"
    circuit_synth_dir.mkdir(exist_ok=True)

    # Create a simple main.py template
    main_py = circuit_synth_dir / "main.py"
    main_py.write_text(f'''#!/usr/bin/env python3
"""
{pcb_name} - Circuit Design
Created with circuit-synth
"""

from circuit_synth import *

@circuit(name="{pcb_name.replace(' ', '_')}")
def main():
    """Main circuit - add your components here"""
    
    # Example: Create a simple LED circuit
    # led = Component(symbol="Device:LED", ref="D", footprint="LED_SMD:LED_0805_2012Metric")
    # resistor = Component(symbol="Device:R", ref="R", value="330", footprint="Resistor_SMD:R_0603_1608Metric")
    # 
    # # Connect LED and resistor
    # gnd = Net("GND")
    # vcc = Net("VCC_3V3")
    # resistor[1] += vcc
    # resistor[2] += led["A"]
    # led["K"] += gnd
    
    pass

if __name__ == "__main__":
    circuit = main()
    circuit.generate_kicad_project(project_name="{pcb_name.replace(' ', '_')}")
''')
    
    console.print(f"[green]✅ Created basic circuit template[/green]")


def copy_complete_claude_setup(pcb_path: Path, pcb_name: str) -> None:
    """Copy the complete .claude directory setup for PCB projects"""
    # Find the circuit-synth root directory
    circuit_synth_root = Path(__file__).parent.parent.parent.parent
    source_claude_dir = circuit_synth_root / ".claude"
    
    if not source_claude_dir.exists():
        console.print("⚠️  Source .claude directory not found - skipping Claude setup", style="yellow")
        return
    
    # Copy .claude directory to PCB project
    dest_claude_dir = pcb_path / ".claude"
    if dest_claude_dir.exists():
        shutil.rmtree(dest_claude_dir)
    
    shutil.copytree(source_claude_dir, dest_claude_dir)
    console.print(f"[green]✅ Copied Claude AI configuration[/green]")


def create_memory_bank_system(pcb_path: Path, pcb_name: str) -> None:
    """Create memory-bank directory structure for automatic documentation"""
    memory_bank_dir = pcb_path / "memory-bank"
    memory_bank_dir.mkdir(exist_ok=True)
    
    # Create memory-bank structure manually (TODO: use MemoryBankManager when implemented)
    for filename in ["decisions.md", "fabrication.md", "testing.md", "timeline.md", "issues.md"]:
        file_path = memory_bank_dir / filename
        file_path.write_text(f"# {filename.replace('.md', '').title()} - {pcb_name}\n\n*This file tracks {filename.replace('.md', '')} for the {pcb_name} project.*\n\n")
    
    console.print(f"[green]✅ Created memory-bank system[/green]")


def create_comprehensive_claude_md(pcb_path: Path, pcb_name: str) -> None:
    """Create comprehensive CLAUDE.md for the PCB project"""
    claude_md = pcb_path / "CLAUDE.md"
    claude_md.write_text(f'''# CLAUDE.md

Project-specific guidance for Claude Code when working with this {pcb_name} project.

## 🚀 Project Overview

This is a **circuit-synth PCB project** for professional circuit design with AI-powered component intelligence.

## ⚡ Quick Commands

```bash
# Run the main circuit
uv run python circuit-synth/main.py

# Test components
uv run python -c "from circuit_synth import *; print('✅ Circuit-synth ready!')"
```

## 🎯 Development

This PCB project uses:
- **Hierarchical circuit design** with separate Python files for each circuit block
- **Memory-bank system** for automatic documentation
- **AI-powered component selection** with JLCPCB integration
- **Professional KiCad integration** with PCB generation

Modify the circuits in `circuit-synth/` to customize your design!

---

**This project is optimized for AI-powered circuit design with Claude Code!** 🎛️
''')
    console.print(f"[green]✅ Created CLAUDE.md[/green]")


def create_pcb_readme(pcb_path: Path, pcb_name: str) -> None:
    """Create README.md for the PCB project"""
    readme_md = pcb_path / "README.md"
    readme_md.write_text(f'''# {pcb_name}

Created with circuit-synth - Professional PCB design with AI assistance.

## Structure

```
{pcb_name.lower().replace(' ', '-')}/
├── circuit-synth/     # Python circuit files
├── memory-bank/       # Automatic documentation
├── .claude/           # AI assistant configuration
├── CLAUDE.md          # Development guide
└── README.md          # This file
```

## Getting Started

```bash
# Generate KiCad project
uv run python circuit-synth/main.py

# Open in KiCad
open {pcb_name.replace(' ', '_')}/{pcb_name.replace(' ', '_')}.kicad_pro
```

## Features

- Professional circuit design with Python
- Automatic KiCad project generation
- AI-powered component selection
- Memory-bank documentation system
- JLCPCB manufacturing integration

Built with [circuit-synth](https://github.com/circuit-synth/circuit-synth) 🚀
''')
    console.print(f"[green]✅ Created README.md[/green]")




@click.command()
@click.argument('pcb_name')
@click.option('--minimal', is_flag=True, help='Create minimal PCB (no examples)')
def main(pcb_name: str, minimal: bool):
    """Create a new PCB development environment.
    
    Examples:
        cs-new-pcb "ESP32 Sensor Board"
        cs-new-pcb "Power Supply Module" --minimal
    """
    
    # Store the original working directory where the command was invoked
    original_cwd = Path.cwd()
    
    console.print(
        Panel.fit(
            Text(f"🚀 Creating PCB: {pcb_name}", style="bold blue"), 
            style="blue"
        )
    )
    
    # Create PCB directory in the original working directory
    pcb_dir_name = pcb_name.lower().replace(' ', '-').replace('_', '-')
    pcb_path = original_cwd / pcb_dir_name
    
    if pcb_path.exists():
        console.print(f"❌ Directory {pcb_dir_name}/ already exists", style="red")
        sys.exit(1)
    
    pcb_path.mkdir()
    console.print(f"📁 Created PCB directory: {pcb_dir_name}/", style="green")
    
    # Create memory-bank system
    console.print("\n🧠 Setting up memory-bank system...", style="yellow")
    create_memory_bank_system(pcb_path, pcb_name)
    
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