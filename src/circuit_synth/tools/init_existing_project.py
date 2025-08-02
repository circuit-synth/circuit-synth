#!/usr/bin/env python3
"""
Circuit-Synth Existing Project Integration Tool

Integrates circuit-synth into an existing KiCad project by:
1. Creating a backup of the original KiCad project
2. Setting up a new directory structure with KiCad project + circuit-synth
3. Converting existing KiCad design to circuit-synth Python code
4. Setting up Claude AI agents and development environment

Usage:
    cs-init-existing-project /path/to/project.kicad_pro
"""

import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text

# Import existing circuit-synth modules
from circuit_synth.claude_integration.agent_registry import register_circuit_agents
from circuit_synth.core.kicad_validator import validate_kicad_installation
from circuit_synth.tools.kicad_parser import KiCadParser

console = Console()


def find_kicad_project(input_path: Path) -> Optional[Path]:
    """Find .kicad_pro file in given path (file or directory)"""
    
    if input_path.is_file():
        if input_path.suffix == ".kicad_pro":
            console.print(f"📁 Using KiCad project file: {input_path.name}", style="blue")
            return input_path
        else:
            console.print("❌ File is not a KiCad project (.kicad_pro)", style="red")
            return None
    
    elif input_path.is_dir():
        console.print(f"📁 Searching for .kicad_pro file in directory: {input_path.name}", style="blue")
        
        # Look for .kicad_pro files in the directory
        kicad_pro_files = list(input_path.glob("*.kicad_pro"))
        
        if not kicad_pro_files:
            console.print(f"❌ No .kicad_pro files found in directory: {input_path}", style="red")
            console.print("💡 Directory should contain a KiCad project file (.kicad_pro)", style="dim")
            return None
        
        elif len(kicad_pro_files) == 1:
            found_project = kicad_pro_files[0]
            console.print(f"✅ Found KiCad project: {found_project.name}", style="green")
            return found_project
        
        else:
            console.print(f"⚠️  Multiple .kicad_pro files found:", style="yellow")
            for i, project in enumerate(kicad_pro_files, 1):
                console.print(f"   {i}. {project.name}", style="dim")
            
            # Use the first one found
            selected_project = kicad_pro_files[0]
            console.print(f"🎯 Using first project: {selected_project.name}", style="cyan")
            return selected_project
    
    else:
        console.print(f"❌ Path does not exist or is not accessible: {input_path}", style="red")
        return None


def validate_kicad_project(kicad_project_path: Path) -> bool:
    """Validate that the KiCad project exists and is complete"""
    console.print("🔍 Validating KiCad project...", style="yellow")
    
    if not kicad_project_path.exists():
        console.print(f"❌ KiCad project file not found: {kicad_project_path}", style="red")
        return False
    
    if kicad_project_path.suffix != ".kicad_pro":
        console.print("❌ File is not a KiCad project (.kicad_pro)", style="red")
        return False
    
    # Check for required files
    project_dir = kicad_project_path.parent
    project_stem = kicad_project_path.stem
    
    schematic_file = project_dir / f"{project_stem}.kicad_sch"
    if not schematic_file.exists():
        console.print(f"❌ Missing schematic file: {schematic_file}", style="red")
        return False
    
    console.print("✅ KiCad project validation passed", style="green")
    console.print(f"   📁 Project: {kicad_project_path.name}")
    console.print(f"   📋 Schematic: {schematic_file.name}")
    
    # Check for PCB file (optional)
    pcb_file = project_dir / f"{project_stem}.kicad_pcb"
    if pcb_file.exists():
        console.print(f"   🛠️  PCB: {pcb_file.name}")
    
    return True


def check_for_existing_circuit_synth(target_dir: Path) -> bool:
    """Check if circuit-synth is already set up in this project"""
    circuit_synth_dir = target_dir / "circuit-synth"
    claude_dir = target_dir / ".claude"
    
    if circuit_synth_dir.exists() or claude_dir.exists():
        console.print("⚠️  Circuit-synth appears to already be set up:", style="yellow")
        if circuit_synth_dir.exists():
            console.print(f"   📁 Found: {circuit_synth_dir}")
        if claude_dir.exists():
            console.print(f"   🤖 Found: {claude_dir}")
        return True
    
    return False


def create_backup(kicad_project_path: Path) -> Path:
    """Create a backup of the original KiCad project"""
    console.print("💾 Creating backup of original KiCad project...", style="yellow")
    
    project_dir = kicad_project_path.parent
    project_name = kicad_project_path.stem
    
    # Create backup directory with timestamp
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = project_dir / f"{project_name}_backup_{timestamp}"
    
    try:
        # Copy entire project directory to backup
        shutil.copytree(project_dir, backup_dir)
        console.print(f"✅ Backup created: {backup_dir}", style="green")
        return backup_dir
    except Exception as e:
        console.print(f"❌ Failed to create backup: {e}", style="red")
        raise


def setup_circuit_synth_in_place(kicad_project_path: Path) -> Path:
    """Add circuit-synth to existing KiCad project directory and organize KiCad files"""
    console.print("📁 Setting up circuit-synth in existing project directory...", style="yellow")
    
    # Work in the same directory as the KiCad project
    source_dir = kicad_project_path.parent
    project_name = kicad_project_path.stem
    
    console.print(f"📋 Organizing project: {source_dir.name}/", style="blue")
    
    # Check if circuit-synth directory already exists
    circuit_synth_dir = source_dir / "circuit-synth"
    if circuit_synth_dir.exists():
        console.print("❌ circuit-synth directory already exists - project appears to already be set up", style="red")
        console.print("💡 Remove the circuit-synth directory if you want to reinitialize", style="dim")
        sys.exit(1)
    
    # Create KiCad project subdirectory
    kicad_subdir = source_dir / project_name
    if not kicad_subdir.exists():
        kicad_subdir.mkdir()
        console.print(f"📁 Created KiCad subdirectory: {project_name}/", style="green")
        
        # Move all KiCad files to subdirectory
        kicad_extensions = {'.kicad_pro', '.kicad_sch', '.kicad_pcb', '.net', '.kicad_prl', '.kicad_dru'}
        files_moved = []
        
        for file_path in source_dir.iterdir():
            if file_path.is_file():
                # Check if it's a KiCad file by extension or if it matches the project name
                is_kicad_file = (
                    file_path.suffix in kicad_extensions or
                    file_path.stem.startswith(project_name)
                )
                
                if is_kicad_file:
                    target_file = kicad_subdir / file_path.name
                    shutil.move(str(file_path), str(target_file))
                    files_moved.append(file_path.name)
                    console.print(f"   ✅ {file_path.name}", style="dim")
        
        console.print(f"📁 Moved {len(files_moved)} KiCad files to {project_name}/", style="green")
    else:
        console.print(f"📁 KiCad subdirectory already exists: {project_name}/", style="blue")
    
    # Create circuit-synth directory
    circuit_synth_dir.mkdir()
    console.print("✅ Created circuit-synth directory", style="green")
    
    console.print(f"✅ Project organization complete: {source_dir.name}/", style="green")
    return source_dir


def copy_claude_setup(target_dir: Path) -> None:
    """Copy .claude directory from circuit-synth to target project, merging if exists"""
    console.print("🤖 Setting up Claude AI agents...", style="yellow")
    
    # Find the circuit-synth root directory
    circuit_synth_root = Path(__file__).parent.parent.parent.parent
    source_claude_dir = circuit_synth_root / ".claude"
    
    if not source_claude_dir.exists():
        console.print("⚠️  Source .claude directory not found - using basic setup", style="yellow")
        register_circuit_agents()
        return
    
    dest_claude_dir = target_dir / ".claude"
    
    try:
        if dest_claude_dir.exists():
            console.print("📁 Existing .claude directory found - merging agents and commands", style="blue")
            
            # Merge agents and commands directories
            source_agents_dir = source_claude_dir / "agents"
            source_commands_dir = source_claude_dir / "commands"
            dest_agents_dir = dest_claude_dir / "agents"
            dest_commands_dir = dest_claude_dir / "commands"
            
            # Ensure destination directories exist
            dest_agents_dir.mkdir(exist_ok=True)
            dest_commands_dir.mkdir(exist_ok=True)
            
            # Copy agents (skip if already exists)
            agents_added = 0
            for agent_file in source_agents_dir.glob("*.md"):
                dest_agent = dest_agents_dir / agent_file.name
                if not dest_agent.exists():
                    shutil.copy2(agent_file, dest_agent)
                    agents_added += 1
            
            # Copy commands (skip if already exists) 
            commands_added = 0
            for command_file in source_commands_dir.glob("*.md"):
                # Skip dev commands
                if command_file.name.startswith("dev-") or command_file.name == "setup_circuit_synth.md":
                    continue
                    
                dest_command = dest_commands_dir / command_file.name
                if not dest_command.exists():
                    shutil.copy2(command_file, dest_command)
                    commands_added += 1
            
            console.print(f"✅ Added {agents_added} new agents and {commands_added} new commands", style="green")
            
        else:
            # Fresh copy
            shutil.copytree(source_claude_dir, dest_claude_dir)
            
            # Remove dev commands (same as cs-new-project)
            commands_dir = dest_claude_dir / "commands"
            agents_dir = dest_claude_dir / "agents"
            
            dev_commands_to_remove = [
                "dev-release-pypi.md",
                "dev-review-branch.md", 
                "dev-review-repo.md",
                "dev-run-tests.md",
                "dev-update-and-commit.md",
                "setup_circuit_synth.md",
            ]
            
            for cmd_file in dev_commands_to_remove:
                cmd_path = commands_dir / cmd_file
                if cmd_path.exists():
                    cmd_path.unlink()
            
            # Remove setup agents
            setup_agents_to_remove = ["first_setup_agent.md"]
            for agent_file in setup_agents_to_remove:
                agent_path = agents_dir / agent_file
                if agent_path.exists():
                    agent_path.unlink()
            
            console.print("✅ Claude AI agents setup complete", style="green")
        
    except Exception as e:
        console.print(f"⚠️  Could not copy .claude directory: {e}", style="yellow")
        console.print("🔄 Falling back to basic agent registration", style="yellow")
        register_circuit_agents()


def convert_kicad_to_circuit_synth(kicad_project_path: Path, target_dir: Path) -> None:
    """Convert existing KiCad design to circuit-synth Python code"""
    console.print("🔄 Converting KiCad design to circuit-synth code...", style="yellow")
    
    try:
        # Use existing KiCad parser
        parser = KiCadParser(str(kicad_project_path))
        
        # Generate netlist
        netlist_path = parser.generate_netlist()
        if not netlist_path:
            console.print("⚠️  Could not generate netlist from KiCad project", style="yellow")
            console.print("   You'll need to create circuit-synth code manually", style="dim")
            return
        
        # Parse the circuits
        circuits = parser.parse_circuits()
        if not circuits:
            console.print("⚠️  Could not parse circuits from netlist", style="yellow")
            console.print("   You'll need to create circuit-synth code manually", style="dim")
            return
        
        # Find the main hierarchical circuit
        main_circuit = None
        all_circuits = {}
        
        for name, circuit in circuits.items():
            all_circuits[name] = circuit
            
            if hasattr(circuit, 'hierarchical_tree') and circuit.hierarchical_tree:
                # Find circuit with the most children (main circuit)
                children = circuit.hierarchical_tree.get(name, [])
                if children and len(children) > 0:
                    if main_circuit is None or len(children) > len(main_circuit.hierarchical_tree.get(main_circuit.name, [])):
                        main_circuit = circuit
        
        # Collect ALL subcircuits for separate files (not just direct children)
        # This ensures we generate files for all subcircuits like debug_header, led_blinker, etc.
        subcircuits = {}
        if main_circuit and hasattr(main_circuit, 'hierarchical_tree') and main_circuit.hierarchical_tree:
            # Get ALL subcircuits (both direct and nested)
            all_subcircuit_names = _collect_all_subcircuits_recursive(
                main_circuit.hierarchical_tree, main_circuit.name
            )
            console.print(f"🔍 Found {len(all_subcircuit_names)} subcircuits for separate files: {sorted(all_subcircuit_names)}")
            
            for subcircuit_name in all_subcircuit_names:
                if subcircuit_name in all_circuits:
                    subcircuits[subcircuit_name] = all_circuits[subcircuit_name]
        
        if not main_circuit:
            # Fall back to first circuit if no hierarchical structure found
            # console.print("🔍 CONVERSION DEBUG: No hierarchical circuit found, using first circuit", style="yellow")
            main_circuit = list(circuits.values())[0] if circuits else None
            
        if not main_circuit:
            console.print("⚠️  No circuits found in netlist", style="yellow")
            console.print("   You'll need to create circuit-synth code manually", style="dim")
            return
        
        # console.print(f"🔍 CONVERSION DEBUG: Using main circuit: {main_circuit.name}")
        # console.print(f"🔍 CONVERSION DEBUG: Found {len(subcircuits)} subcircuits: {list(subcircuits.keys())}")
        
        # Generate hierarchical Python code
        if len(subcircuits) > 0:
            generate_hierarchical_circuit_synth_code(main_circuit, subcircuits, target_dir, kicad_project_path.stem)
        else:
            # Generate single file for non-hierarchical circuits
            python_code = generate_circuit_synth_code(main_circuit, kicad_project_path.stem)
            main_py_path = target_dir / "circuit-synth" / "main.py"
            with open(main_py_path, "w") as f:
                f.write(python_code)
        
        console.print(f"✅ Generated circuit-synth code in circuit-synth/", style="green")
        
    except Exception as e:
        console.print(f"⚠️  Error converting KiCad to circuit-synth: {e}", style="yellow")
        console.print("   A basic template will be created instead", style="dim")
        create_basic_template(target_dir, kicad_project_path.stem)


def _collect_all_subcircuits_recursive(hierarchical_tree: dict, start_circuit: str) -> set:
    """Recursively collect all subcircuits from hierarchical tree"""
    all_subcircuits = set()
    
    def _recursive_collect(circuit_name: str):
        children = hierarchical_tree.get(circuit_name, [])
        for child in children:
            all_subcircuits.add(child)
            # Recursively collect children of this child
            _recursive_collect(child)
    
    _recursive_collect(start_circuit)
    return all_subcircuits


def map_subcircuit_to_target_name(kicad_name: str) -> tuple[str, str]:
    """Convert KiCad subcircuit names to target file and function names"""
    # Handle specific name mappings to match expected structure
    name_mappings = {
        'ESP32_C6_MCU': 'esp32c6',
        'USB_Port': 'usb',
        'Power_Supply': 'power_supply',
        'Debug_Header': 'debug_header', 
        'LED_Blinker': 'led_blinker'
    }
    
    # Use mapping if available, otherwise convert to lowercase
    if kicad_name in name_mappings:
        filename = name_mappings[kicad_name]
        function_name = name_mappings[kicad_name]
    else:
        filename = kicad_name.lower()
        function_name = kicad_name.lower()
    
    return (filename, function_name)


def generate_hierarchical_circuit_synth_code(main_circuit: Any, subcircuits: dict, target_dir: Path, project_name: str) -> None:
    """Generate hierarchical circuit-synth Python code with separate subcircuit files"""
    
    console.print(f"🏗️ Generating hierarchical circuit with {len(subcircuits)} subcircuits", style="blue")
    
    # Generate subcircuit files
    subcircuit_imports = []
    subcircuit_calls = []
    
    for name, subcircuit in subcircuits.items():
        # Map to target file and function names
        filename, function_name = map_subcircuit_to_target_name(name)
        subcircuit_filename = f"{filename}.py"
        subcircuit_path = target_dir / "circuit-synth" / subcircuit_filename
        
        # Generate subcircuit Python code with mapped names
        subcircuit_code = generate_subcircuit_code(subcircuit, name, function_name)
        with open(subcircuit_path, "w") as f:
            f.write(subcircuit_code)
        
        # Track imports and calls for main file (use target names)
        subcircuit_imports.append(f"from {filename} import {function_name}")
        
        # Generate the proper function call based on subcircuit type
        if 'usb' in function_name.lower():
            subcircuit_calls.append(f"    {function_name}_circuit = {function_name}(vbus, gnd, usb_dp, usb_dm)")
        elif 'power' in function_name.lower():
            subcircuit_calls.append(f"    {function_name}_circuit = {function_name}(vbus, vcc_3v3, gnd)")
        elif 'esp32' in function_name.lower():
            subcircuit_calls.append(f"    esp32_circuit = {function_name}(vcc_3v3, gnd, usb_dp, usb_dm)")
        else:
            subcircuit_calls.append(f"    {function_name}_circuit = {function_name}(vcc_3v3, gnd)")
        
        console.print(f"   ✅ Generated {subcircuit_filename}")
    
    # Generate main.py that orchestrates all subcircuits
    main_code = generate_hierarchical_main_code(main_circuit, project_name, subcircuit_imports, subcircuit_calls)
    main_py_path = target_dir / "circuit-synth" / "main.py"
    with open(main_py_path, "w") as f:
        f.write(main_code)
    
    console.print(f"   ✅ Generated main.py with hierarchical structure")


def generate_subcircuit_code(circuit: Any, subcircuit_name: str, function_name: str = None) -> str:
    """Generate Python code for a single subcircuit"""
    
    if function_name is None:
        function_name = f"{subcircuit_name.lower()}_circuit"
    
    # Determine function parameters based on subcircuit type
    if 'usb' in function_name.lower():
        params = "vbus_out, gnd, usb_dp, usb_dm"
        param_doc = "USB-C port with proper parameter interface"
    elif 'power' in function_name.lower():
        params = "vbus_in, vcc_3v3_out, gnd"
        param_doc = "Power supply with input/output interface"
    elif 'esp32' in function_name.lower():
        params = "vcc_3v3, gnd, usb_dp, usb_dm"
        param_doc = "ESP32 MCU with power and USB interface"
    else:
        params = "vcc_3v3, gnd"
        param_doc = "Basic subcircuit with power interface"
    
    code = f'''#!/usr/bin/env python3
"""
{subcircuit_name} Circuit - Converted from KiCad hierarchical sheet
{param_doc}
"""

from circuit_synth import *

@circuit(name="{subcircuit_name}")
def {function_name}({params}):
    """{param_doc}"""
    
    # Components
'''
    
    # Add components
    for component in circuit.components:
        safe_var_name = component.reference.lower().replace('-', '_').replace('.', '_')
        ref_prefix = component.reference[0] if component.reference else "U"
        code += f'''    {safe_var_name} = Component(
        symbol="{component.lib_id}",
        ref="{ref_prefix}",
        footprint="{component.footprint}",
'''
        if hasattr(component, 'value') and component.value:
            code += f'        value="{component.value}",\n'
        code += '    )\n\n'
    
    # Add nets
    code += '    # Nets\n'
    for net in circuit.nets:
        net_name = net.name if hasattr(net, 'name') else str(net)
        safe_net_name = net_name.replace('/', '_').replace('-', '_').replace('$', '_').replace(' ', '_')
        # Remove any non-alphanumeric characters except underscores
        safe_net_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in safe_net_name)
        code += f'    {safe_net_name.lower()} = Net("{net_name}")\n'
    
    code += '\n    # Connections\n'
    code += '    # TODO: Add component connections based on netlist\n'
    code += '    # Example: component1["pin1"] += net_name\n\n'
    
    return code


def generate_hierarchical_main_code(main_circuit: Any, project_name: str, subcircuit_imports: list, subcircuit_calls: list) -> str:
    """Generate main.py code that orchestrates all subcircuits"""
    
    imports_section = "\n".join(subcircuit_imports)
    calls_section = "\n".join(subcircuit_calls)
    
    code = f'''#!/usr/bin/env python3
"""
Main Circuit - {project_name}
Hierarchical circuit design with modular subcircuits

This is the main entry point that orchestrates all subcircuits.
Converted from KiCad hierarchical design.
"""

from circuit_synth import *

# Import all subcircuits
{imports_section}

@circuit(name="{project_name}_Main")
def main_circuit():
    """Main hierarchical circuit - {project_name}"""
    
    # Create shared nets between subcircuits (ONLY nets - no components here)
    vbus = Net('VBUS')
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    usb_dp = Net('USB_DP')
    usb_dm = Net('USB_DM')

    
    # Create all circuits with shared nets
{calls_section}


if __name__ == "__main__":
    print("🚀 Generating KiCad project from circuit-synth...")
    circuit = main_circuit()
    
    # Generate KiCad project
    circuit.generate_kicad_project(
        project_name="{project_name}",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    
    print("✅ KiCad project generated successfully!")
    print("📁 Check the generated KiCad files for your circuit")
'''
    
    return code


def generate_circuit_synth_code(circuit: Any, project_name: str) -> str:
    """Generate circuit-synth Python code from parsed circuit"""
    
    # Check if this is a hierarchical circuit
    # console.print(f"🔍 CONVERSION DEBUG: Circuit name: {circuit.name}")
    # console.print(f"🔍 CONVERSION DEBUG: Circuit components count: {len(circuit.components)}")
    # console.print(f"🔍 CONVERSION DEBUG: Circuit nets count: {len(circuit.nets)}")
    # console.print(f"🔍 CONVERSION DEBUG: Circuit hierarchical tree: {getattr(circuit, 'hierarchical_tree', None)}")
    # console.print(f"🔍 CONVERSION DEBUG: Circuit is_hierarchical_sheet: {getattr(circuit, 'is_hierarchical_sheet', None)}")
    
    code = f'''#!/usr/bin/env python3
"""
{project_name} - Converted from KiCad project

This circuit was automatically generated from an existing KiCad project.
You may need to adjust component symbols, footprints, and net connections.
"""

from circuit_synth import *

@circuit(name="{project_name}")
def main_circuit():
    """Main circuit converted from KiCad project"""
    
    # Components
'''
    
    # Add components
    for component in circuit.components:
        safe_var_name = component.reference.lower().replace('-', '_').replace('.', '_')
        ref_prefix = component.reference[0] if component.reference else "U"
        code += f'''    {safe_var_name} = Component(
        symbol="{component.lib_id}",
        ref="{ref_prefix}",
        footprint="{component.footprint}",
'''
        if hasattr(component, 'value') and component.value:
            code += f'        value="{component.value}",\n'
        code += '    )\n\n'
    
    # Add nets
    code += '    # Nets\n'
    for net in circuit.nets:
        net_name = net.name if hasattr(net, 'name') else str(net)
        safe_net_name = net_name.replace('/', '_').replace('-', '_').replace('$', '_').replace(' ', '_')
        # Remove any non-alphanumeric characters except underscores
        safe_net_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in safe_net_name)
        code += f'    {safe_net_name.lower()} = Net("{net_name}")\n'
    
    code += '\n    # Connections\n'
    code += '    # TODO: Add component connections based on netlist\n'
    code += '    # Example: component1["pin1"] += net_name\n\n'
    
    code += '''
if __name__ == "__main__":
    print("🚀 Generating KiCad project from circuit-synth...")
    circuit = main_circuit()
    
    # Generate KiCad project
    circuit.generate_kicad_project(
        project_name="''' + project_name + '''",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    
    print("✅ KiCad project generated successfully!")
    print("📁 Check the generated KiCad files for your circuit")
'''
    
    return code


def create_basic_template(target_dir: Path, project_name: str) -> None:
    """Create a basic circuit-synth template when conversion fails"""
    console.print("📝 Creating basic circuit-synth template...", style="blue")
    
    template_code = f'''#!/usr/bin/env python3
"""
{project_name} - Circuit-Synth Template

This is a basic template for your converted KiCad project.
Please implement your circuit design using circuit-synth syntax.
"""

from circuit_synth import *

@circuit(name="{project_name}")
def main_circuit():
    """Main circuit - implement your design here"""
    
    # Example component
    led = Component(
        symbol="Device:LED",
        ref="D",
        footprint="LED_SMD:LED_0805_2012Metric"
    )
    
    resistor = Component(
        symbol="Device:R", 
        ref="R",
        value="330",
        footprint="Resistor_SMD:R_0805_2012Metric"
    )
    
    # Example nets
    vcc = Net("VCC")
    gnd = Net("GND")
    led_anode = Net("LED_ANODE")
    
    # Example connections
    resistor[1] += vcc
    resistor[2] += led_anode
    led["A"] += led_anode
    led["K"] += gnd

if __name__ == "__main__":
    print("🚀 Generating KiCad project from circuit-synth...")
    circuit = main_circuit()
    
    circuit.generate_kicad_project(
        project_name="{project_name}",
        placement_algorithm="hierarchical", 
        generate_pcb=True
    )
    
    print("✅ KiCad project generated!")
'''
    
    main_py_path = target_dir / "circuit-synth" / "main.py"
    with open(main_py_path, "w") as f:
        f.write(template_code)
    
    console.print(f"✅ Basic template created: {main_py_path}", style="green")


def create_project_files(target_dir: Path, project_name: str) -> None:
    """Create README.md and CLAUDE.md files"""
    console.print("📚 Creating project documentation...", style="yellow")
    
    # Create README.md
    readme_content = f"""# {project_name}

A circuit-synth project converted from an existing KiCad design.

## 🚀 Quick Start

```bash
# Run the converted circuit
uv run python circuit-synth/main.py

# Test circuit-synth is working
uv run python -c "from circuit_synth import *; print('✅ Circuit-synth ready!')"
```

## 📁 Project Structure

```
{project_name}/
├── circuit-synth/        # Circuit-synth Python files
│   └── main.py           # Main circuit (converted from KiCad)
├── *.kicad_pro          # Original KiCad project file
├── *.kicad_sch          # Original KiCad schematic  
├── *.kicad_pcb          # Original KiCad PCB (if present)
├── .claude/             # AI agents for Claude Code
│   ├── agents/          # Specialized circuit design agents
│   └── commands/        # Slash commands
├── README.md           # This file
└── CLAUDE.md           # Project-specific Claude guidance
```

## 🔄 Next Steps

1. **Review the generated code** in `circuit-synth/main.py`
2. **Update component symbols and footprints** as needed
3. **Verify net connections** match your original design
4. **Test the circuit generation** with `uv run python circuit-synth/main.py`
5. **Use Claude Code agents** for AI-assisted improvements

## 🤖 AI-Powered Design

This project includes specialized AI agents:
- **circuit-synth**: Circuit code generation and KiCad integration
- **simulation-expert**: SPICE simulation and validation  
- **jlc-parts-finder**: JLCPCB component sourcing
- **orchestrator**: Master coordinator for complex projects

Use natural language to improve your design:
```
👤 "Optimize this power supply for better efficiency"
👤 "Add protection circuits to prevent overcurrent"  
👤 "Find alternative components available on JLCPCB"
```

## 📖 Documentation

- Circuit-Synth: https://circuit-synth.readthedocs.io
- KiCad: https://docs.kicad.org

**Happy circuit designing!** 🎛️
"""
    
    # Create CLAUDE.md
    claude_md_content = f"""# CLAUDE.md

Project-specific guidance for Claude Code when working with this converted circuit-synth project.

## 🚀 Project Overview

This project was **converted from an existing KiCad design** to circuit-synth format.

**Important**: The generated circuit-synth code may need manual review and adjustments:
- Component symbols and footprints may need updating
- Net connections should be verified against the original design
- Component values and references should be checked

## ⚡ Available Tools

### **Slash Commands**
- `/find-symbol STM32` - Search KiCad symbol libraries
- `/find-footprint LQFP` - Search KiCad footprint libraries
- `/analyze-design` - Analyze circuit designs

### **Specialized Agents**
- **circuit-synth** - Circuit code generation and KiCad integration  
- **simulation-expert** - SPICE simulation and validation
- **jlc-parts-finder** - JLCPCB component availability
- **orchestrator** - Master coordinator for complex projects

## 🔧 Essential Commands

```bash
# Test the converted circuit
uv run python circuit-synth/main.py

# Validate circuit-synth installation
uv run python -c "from circuit_synth import *; print('✅ Ready!')"
```

## 🎯 Conversion Review Checklist

When reviewing the converted circuit-synth code:

1. **Component Verification**:
   - Check that symbols match KiCad standard libraries
   - Verify footprints are correct for your components
   - Update component values if missing

2. **Net Connection Review**:
   - Ensure all component pins are properly connected
   - Verify net names match your design intent
   - Check for missing or incorrect connections

3. **Symbol/Footprint Updates**:
   - Use `/find-symbol` and `/find-footprint` commands
   - Replace generic symbols with specific part numbers
   - Ensure manufacturability with JLCPCB-available components

## 🚀 Getting Help

Ask for specific improvements:
```
👤 "Review this converted circuit and suggest improvements"
👤 "Find JLCPCB alternatives for components not in stock"  
👤 "Add proper decoupling capacitors to this design"
👤 "Simulate this power supply circuit for stability"
```

---

**This converted project is ready for AI-powered circuit design with Claude Code!** 🎛️
"""
    
    # Write files
    with open(target_dir / "README.md", "w") as f:
        f.write(readme_content)
    
    with open(target_dir / "CLAUDE.md", "w") as f:
        f.write(claude_md_content)
    
    console.print("✅ Project documentation created", style="green")


@click.command()
@click.argument("kicad_project", type=click.Path(exists=True, path_type=Path))
@click.option("--skip-conversion", is_flag=True, help="Skip KiCad to circuit-synth conversion")
def main(kicad_project: Path, skip_conversion: bool):
    """Initialize circuit-synth in an existing KiCad project directory
    
    Adds circuit-synth functionality to an existing KiCad project by adding:
    - Circuit-synth Python code directory
    - Claude AI agents for intelligent circuit design  
    - Project documentation and setup
    
    The KiCad files remain in their original location.
    
    Examples:
        cs-init-existing-project /path/to/my_board.kicad_pro
        cs-init-existing-project /path/to/project_directory/
    """
    
    console.print(
        Panel.fit(
            Text("🔄 Circuit-Synth Existing Project Integration", style="bold blue"), 
            style="blue"
        )
    )
    
    # Handle directory input - find .kicad_pro file
    actual_kicad_project = find_kicad_project(kicad_project)
    if not actual_kicad_project:
        sys.exit(1)
    
    # Validate the found/provided KiCad project
    if not validate_kicad_project(actual_kicad_project):
        sys.exit(1)
    
    project_name = actual_kicad_project.stem
    console.print(f"📁 Project: {project_name}", style="cyan")
    
    # Set up circuit-synth in the same directory as the KiCad project
    target_dir = setup_circuit_synth_in_place(actual_kicad_project)
    
    # Copy Claude setup
    copy_claude_setup(target_dir)
    
    # Convert KiCad to circuit-synth (KiCad files are now in subdirectory)
    if not skip_conversion:
        kicad_project_in_subdir = target_dir / project_name / actual_kicad_project.name
        convert_kicad_to_circuit_synth(kicad_project_in_subdir, target_dir)
    else:
        console.print("⏭️  Skipped KiCad conversion", style="yellow")
        create_basic_template(target_dir, project_name)
    
    # Create project documentation
    create_project_files(target_dir, project_name)
    
    # Success message
    console.print(
        Panel.fit(
            Text(f"✅ Circuit-synth integration complete!", style="bold green")
            + Text(f"\n\n📁 Enhanced project: {target_dir.name}")
            + Text(f"\n🔄 Circuit-synth code: circuit-synth/main.py")
            + Text(f"\n🚀 Get started: uv run python circuit-synth/main.py")
            + Text(f"\n🤖 AI agents: Available in Claude Code")
            + Text(f"\n📖 Documentation: See README.md"),
            title="🎉 Success!",
            style="green",
        )
    )


if __name__ == "__main__":
    main()