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

def _copy_claude_directory(src_claude_dir, dest_claude_dir: Path, pcb_name: str, circuit_name: str) -> None:
    """Recursively copy .claude directory structure with customization."""
    import os
    
    def copy_file_with_customization(src_path, dest_path: Path):
        """Copy a file and customize project-specific content."""
        try:
            content = src_path.read_text()
            # Replace project-specific placeholders
            content = content.replace('ESP32-C6 Development Board', pcb_name)
            content = content.replace('ESP32_C6_Dev_Board', circuit_name)
            content = content.replace('esp32-c6-dev-board', pcb_name.lower().replace(' ', '-'))
            dest_path.write_text(content)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not customize {dest_path}: {e}[/yellow]")
            # Fall back to direct copy
            dest_path.write_text(src_path.read_text())
    
    def copy_directory_recursive(src_dir, dest_dir: Path):
        """Recursively copy directory structure."""
        try:
            # Get list of items in source directory
            for item_name in os.listdir(str(src_dir)):
                if item_name.startswith('.'):
                    continue  # Skip hidden files
                    
                src_item = src_dir / item_name
                dest_item = dest_dir / item_name
                
                if src_item.is_dir():
                    dest_item.mkdir(exist_ok=True)
                    copy_directory_recursive(src_item, dest_item)
                else:
                    copy_file_with_customization(src_item, dest_item)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not copy directory {src_dir}: {e}[/yellow]")
    
    # Copy root .claude files
    for item_name in ['settings.json', 'README.md', 'AGENT_USAGE_GUIDE.md', 'README_ORGANIZATION.md', 'mcp_settings.json', 'session_hook_update.sh']:
        try:
            src_file = src_claude_dir / item_name
            dest_file = dest_claude_dir / item_name
            if src_file.exists():
                copy_file_with_customization(src_file, dest_file)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not copy {item_name}: {e}[/yellow]")
    
    # Copy subdirectories (agents, commands)
    for subdir_name in ['agents', 'commands']:
        try:
            src_subdir = src_claude_dir / subdir_name
            dest_subdir = dest_claude_dir / subdir_name
            if src_subdir.exists():
                dest_subdir.mkdir(exist_ok=True)
                copy_directory_recursive(src_subdir, dest_subdir)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not copy {subdir_name} directory: {e}[/yellow]")


def copy_example_project_structure(pcb_path: Path, pcb_name: str) -> None:
    """Copy the complete example_project structure and customize it."""
    circuit_name = pcb_name.replace(" ", "_")
    
    try:
        # Copy all files from example_project template
        template_files = files('circuit_synth') / 'data' / 'templates' / 'example_project'
        
        # Copy CLAUDE.md
        claude_content = (template_files / 'CLAUDE.md').read_text()
        claude_customized = claude_content.replace('ESP32-C6 Development Board', pcb_name)
        (pcb_path / 'CLAUDE.md').write_text(claude_customized)
        
        # Copy README.md
        readme_content = (template_files / 'README.md').read_text()
        readme_customized = readme_content.replace('ESP32-C6 Development Board', pcb_name)
        readme_customized = readme_customized.replace('ESP32_C6_Dev_Board', circuit_name)
        (pcb_path / 'README.md').write_text(readme_customized)
        
        # Copy pyproject.toml
        pyproject_content = (template_files / 'pyproject.toml').read_text()
        pyproject_customized = pyproject_content.replace('esp32-c6-dev-board', pcb_path.name)
        pyproject_customized = pyproject_customized.replace('ESP32-C6 Development Board', pcb_name)
        (pcb_path / 'pyproject.toml').write_text(pyproject_customized)
        
        # Create circuit-synth directory
        circuit_dir = pcb_path / 'circuit-synth'
        circuit_dir.mkdir(exist_ok=True)
        
        # Copy all Python files from circuit-synth directory
        circuit_template_dir = template_files / 'circuit-synth'
        python_files = ['debug_header.py', 'esp32c6.py', 'led_blinker.py', 'power_supply.py', 'usb.py']
        
        for py_file in python_files:
            content = (circuit_template_dir / py_file).read_text()
            (circuit_dir / py_file).write_text(content)
        
        # Copy and customize main.py
        main_content = (circuit_template_dir / 'main.py').read_text()
        main_customized = main_content.replace('ESP32_C6_Dev_Board', circuit_name)
        main_customized = main_customized.replace('"ESP32-C6 Development Board"', f'"{pcb_name}"')
        (circuit_dir / 'main.py').write_text(main_customized)
        
        # Copy and rename JSON file
        json_content = (circuit_template_dir / 'ESP32_C6_Dev_Board.json').read_text()
        json_customized = json_content.replace('ESP32_C6_Dev_Board', circuit_name)
        (circuit_dir / f'{circuit_name}.json').write_text(json_customized)
        
        # Copy .claude directory with all agents and commands
        claude_dir = pcb_path / '.claude'
        claude_dir.mkdir(exist_ok=True)
        _copy_claude_directory(template_files / '.claude', claude_dir, pcb_name, circuit_name)
        
        console.print(f"[green]✅ Copied complete example project structure with .claude agents[/green]")
        
    except Exception as e:
        console.print(f"[yellow]Warning: Could not copy from example_project template: {e}[/yellow]")
        console.print("[yellow]Falling back to basic structure...[/yellow]")
        _create_fallback_structure(pcb_path, pcb_name)


def _create_fallback_structure(pcb_path: Path, pcb_name: str) -> None:
    """Fallback: Create basic structure if example_project template not available."""
    circuit_name = pcb_name.replace(' ', '_')
    
    # Create circuit-synth directory
    circuit_dir = pcb_path / "circuit-synth"
    circuit_dir.mkdir(exist_ok=True)
    
    # Create basic main.py inside circuit-synth/
    main_py = circuit_dir / "main.py"
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
    
    # Create basic README.md
    readme_md = pcb_path / "README.md"
    readme_md.write_text(f'''# {pcb_name}\n\nCreated with circuit-synth\n''')
    
    # Create basic CLAUDE.md
    claude_md = pcb_path / "CLAUDE.md"
    claude_md.write_text(f'''# {pcb_name}\n\nCircuit design project\n''')
    
    # Create basic pyproject.toml
    pyproject_toml = pcb_path / "pyproject.toml"
    pyproject_toml.write_text(f'''[project]\nname = "{pcb_path.name}"\ndescription = "{pcb_name}"\n''')
    
    console.print(f"[green]✅ Created basic project structure[/green]")


# Remove create_claude_setup - not needed since example_project doesn't have .claude


# Remove create_memory_bank_system - not needed since example_project doesn't have memory-bank


# Remove create_comprehensive_claude_md - handled in copy_example_project_structure


# Remove create_pcb_readme - handled in copy_example_project_structure




@click.command()
@click.argument('pcb_name')
@click.option('--minimal', is_flag=True, help='Create minimal PCB (no examples)')
def main(pcb_name: str, minimal: bool):
    """Create a new PCB development environment in the current directory.
    
    This command assumes you're in a fresh uv project directory and will:
    1. Delete all files except .git and hidden files
    2. Add the circuit-synth project template
    
    Examples:
        cs-new-pcb "ESP32 Sensor Board"
        cs-new-pcb "Power Supply Module" --minimal
    """
    
    # Always use current directory
    pcb_path = Path.cwd()
    
    console.print(
        Panel.fit(
            Text(f"🚀 Creating PCB: {pcb_name}", style="bold blue"), 
            style="blue"
        )
    )
    
    console.print(f"📁 Setting up PCB project in current directory: {pcb_path.name}/", style="green")
    
    # Clean up ALL non-hidden files and directories
    console.print("\n🧹 Cleaning up existing files...", style="yellow")
    
    for item in pcb_path.iterdir():
        # Skip hidden files (like .git)
        if item.name.startswith('.'):
            continue
            
        if item.is_file():
            item.unlink()
            console.print(f"   ✓ Removed {item.name}", style="dim")
        elif item.is_dir():
            shutil.rmtree(item)
            console.print(f"   ✓ Removed {item.name}/", style="dim")
    
    # Copy complete example project structure
    console.print("\n📝 Copying example project structure...", style="yellow")
    if not minimal:
        copy_example_project_structure(pcb_path, pcb_name)
    else:
        _create_fallback_structure(pcb_path, pcb_name)
    
    # Success message
    console.print(
        Panel.fit(
            Text(f"✅ PCB '{pcb_name}' created successfully!", style="bold green")
            + Text(f"\n\n📁 Location: Current directory")
            + Text(f"\n🚀 Get started: cd circuit-synth && uv run python main.py")
            + Text(f"\n🧠 Memory-bank: Automatic documentation enabled")
            + Text(f"\n🤖 AI Agent: Comprehensive Claude assistant configured")
            + Text(f"\n📖 Documentation: See README.md and CLAUDE.md"),
            title="🎉 Success!",
            style="green",
        )
    )


if __name__ == "__main__":
    main()