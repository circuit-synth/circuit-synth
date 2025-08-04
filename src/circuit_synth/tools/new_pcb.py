#!/usr/bin/env python3
"""
Circuit-Synth New PCB Setup Tool

Creates a complete PCB development environment with:
- Circuit-synth Python circuit file
- Memory-bank system for automatic documentation
- Claude AI agent for PCB-specific assistance
- Comprehensive CLAUDE.md with all commands
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

try:
    from importlib.resources import files
except ImportError:
    # Fallback for Python < 3.9
    from importlib_resources import files

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def get_template_content(template_name: str) -> str:
    """Get content of bundled template file."""
    try:
        # Use modern importlib.resources
        template_files = files('circuit_synth') / 'data' / 'templates' / template_name
        return template_files.read_text()
    except Exception:
        # Fallback for development environment
        current_file = Path(__file__).resolve()
        repo_root = current_file.parent.parent.parent.parent
        template_path = repo_root / "src" / "circuit_synth" / "data" / "templates" / template_name
        return template_path.read_text()

def create_project_files(pcb_path: Path, pcb_name: str) -> None:
    """Create main project files from templates."""
    circuit_name = pcb_name.replace(" ", "_")
    project_dir = pcb_path.name
    
    # Create main.py from template
    try:
        template_content = get_template_content("project/main.py")
        
        main_content = template_content.format(
            project_name=pcb_name,
            circuit_name=circuit_name
        )
        
        main_py = pcb_path / "main.py"
        main_py.write_text(main_content)
        console.print(f"[green]✅ Created main.py circuit file[/green]")
        
    except Exception as e:
        console.print(f"[yellow]Warning: Could not create from template: {e}[/yellow]")
        console.print("[yellow]Creating basic circuit file...[/yellow]")
        _create_basic_circuit_file(pcb_path, pcb_name)


def _create_basic_circuit_file(pcb_path: Path, pcb_name: str) -> None:
    """Fallback: Create basic circuit file if templates not available."""
    circuit_name = pcb_name.replace(' ', '_')
    
    # Create a simple main.py template
    main_py = pcb_path / "main.py"
    main_py.write_text(f'''#!/usr/bin/env python3
"""
{pcb_name} - Circuit Design
Created with circuit-synth
"""

from circuit_synth import *

@circuit(name="{circuit_name}")
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
    circuit.generate_kicad_project(project_name="{circuit_name}")
''')
    
    console.print(f"[green]✅ Created basic circuit file[/green]")


def create_claude_setup(pcb_path: Path, pcb_name: str) -> None:
    """Create .claude directory setup for PCB projects"""
    dest_claude_dir = pcb_path / ".claude"
    dest_claude_dir.mkdir(exist_ok=True)
    
    try:
        # Copy MCP settings from template
        mcp_content = get_template_content("claude/mcp_settings.json")
        
        mcp_file = dest_claude_dir / "mcp_settings.json"
        mcp_file.write_text(mcp_content)
        console.print(f"[green]✅ Created Claude AI configuration[/green]")
        
    except Exception as e:
        console.print(f"[yellow]Warning: Could not create Claude config from template: {e}[/yellow]")
        # Create basic MCP settings
        mcp_file = dest_claude_dir / "mcp_settings.json"
        mcp_file.write_text('{}') 
        console.print(f"[green]✅ Created basic Claude configuration[/green]")


def create_memory_bank_system(pcb_path: Path, pcb_name: str) -> None:
    """Create memory-bank directory structure for automatic documentation"""
    memory_bank_dir = pcb_path / "memory-bank"
    memory_bank_dir.mkdir(exist_ok=True)
    
    # Create memory-bank files from templates
    for filename in ["decisions.md", "fabrication.md", "testing.md", "timeline.md", "issues.md"]:
        try:
            template_content = get_template_content(f"memory_bank/{filename}")
            content = template_content.format(project_name=pcb_name)
            file_path = memory_bank_dir / filename
            file_path.write_text(content)
            
        except Exception:
            # Fallback to basic content
            file_path = memory_bank_dir / filename
            file_path.write_text(f"# {filename.replace('.md', '').title()} - {pcb_name}\n\n*This file tracks {filename.replace('.md', '')} for the {pcb_name} project.*\n\n")
    
    console.print(f"[green]✅ Created memory-bank system[/green]")


def create_comprehensive_claude_md(pcb_path: Path, pcb_name: str) -> None:
    """Create comprehensive CLAUDE.md for the PCB project"""
    try:
        template_content = get_template_content("project/CLAUDE.md")
        claude_content = template_content.format(project_name=pcb_name)
        claude_md = pcb_path / "CLAUDE.md"
        claude_md.write_text(claude_content)
        console.print(f"[green]✅ Created CLAUDE.md[/green]")
        
    except Exception:
        # Fallback to basic CLAUDE.md
        claude_md = pcb_path / "CLAUDE.md"
        claude_md.write_text(f'''# CLAUDE.md

Project-specific guidance for Claude Code when working with this {pcb_name} project.

## 🚀 Project Overview

This is a **circuit-synth PCB project** for professional circuit design with AI-powered component intelligence.

## ⚡ Quick Commands

```bash
# Run the main circuit
uv run python main.py

# Test components
uv run python -c "from circuit_synth import *; print('✅ Circuit-synth ready!')"
```

## 🎯 Development

This PCB project uses:
- **Python-based circuit design** with intuitive component creation
- **Memory-bank system** for automatic documentation
- **AI-powered component selection** with JLCPCB integration
- **Professional KiCad integration** with PCB generation

Modify the circuits in `main.py` to customize your design!

---

**This project is optimized for AI-powered circuit design with Claude Code!** 🎛️
''')
        console.print(f"[green]✅ Created CLAUDE.md[/green]")


def create_pcb_readme(pcb_path: Path, pcb_name: str) -> None:
    """Create README.md for the PCB project"""
    try:
        template_content = get_template_content("project/README.md")
        circuit_name = pcb_name.replace(' ', '_')
        project_dir = pcb_path.name
        
        readme_content = template_content.format(
            project_name=pcb_name,
            project_dir=project_dir,
            circuit_name=circuit_name
        )
        
        readme_md = pcb_path / "README.md"
        readme_md.write_text(readme_content)
        console.print(f"[green]✅ Created README.md[/green]")
        
    except Exception:
        # Fallback to basic README
        circuit_name = pcb_name.replace(' ', '_')
        project_dir = pcb_path.name
        readme_md = pcb_path / "README.md"
        readme_md.write_text(f'''# {pcb_name}

Created with circuit-synth - Professional PCB design with AI assistance.

## Structure

```
{project_dir}/
├── main.py            # Main circuit design file
├── memory-bank/       # Automatic documentation
├── .claude/           # AI assistant configuration
├── CLAUDE.md          # Development guide
└── README.md          # This file
```

## Getting Started

```bash
# Generate KiCad project
uv run python main.py

# Open in KiCad
open {circuit_name}/{circuit_name}.kicad_pro
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
    
    # Create Claude setup
    console.print("\n🤖 Setting up AI assistant...", style="yellow")
    create_claude_setup(pcb_path, pcb_name)
    
    # Create comprehensive CLAUDE.md  
    console.print("\n📋 Creating comprehensive CLAUDE.md...", style="yellow")
    create_comprehensive_claude_md(pcb_path, pcb_name)
    
    # Create project files
    console.print("\n📝 Creating circuit files...", style="yellow")
    if not minimal:
        create_project_files(pcb_path, pcb_name)
    else:
        _create_basic_circuit_file(pcb_path, pcb_name)
    
    # Create README
    console.print("\n📚 Creating documentation...", style="yellow")
    create_pcb_readme(pcb_path, pcb_name)
    
    # Success message
    console.print(
        Panel.fit(
            Text(f"✅ PCB '{pcb_name}' created successfully!", style="bold green")
            + Text(f"\n\n📁 Location: {pcb_path}")
            + Text(f"\n🚀 Get started: cd {pcb_dir_name} && uv run python main.py")
            + Text(f"\n🧠 Memory-bank: Automatic documentation enabled")
            + Text(f"\n🤖 AI Agent: Comprehensive Claude assistant configured")
            + Text(f"\n📖 Documentation: See README.md and CLAUDE.md"),
            title="🎉 Success!",
            style="green",
        )
    )


if __name__ == "__main__":
    main()